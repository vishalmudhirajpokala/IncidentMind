"""Agent service: the incident response loop.

This module owns the vertical slice end to end:

    incident -> signals -> memory recall -> historical evidence -> analysis
             -> recommendation -> human approval -> simulated action
             -> resolution -> retain to memory

Two rules shape the code here:

  * Nothing is executed. The only action surface is the simulated, explicitly
    human-approved one. There is no code path in this service (or anywhere
    else) that touches production infrastructure.
  * Nothing is overclaimed. When a provider is unavailable the response says so
    and the analysis degrades; it never pretends a memory was recalled or that
    a model produced something it did not.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlmodel import Session

from app.config import Settings, settings as default_settings
from app.integrations.factory import get_action_provider, get_llm_provider
from app.integrations.base import LLMProvider
from app.models.incident import Incident, utcnow
from app.prompts import render
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.schemas.agent import (
    InvestigationResult,
    ResolveRequest,
    ResolveResponse,
    SimulatedActionRequest,
    SimulatedActionResult,
    TelemetryPoint,
)
from app.schemas.llm import LLMInvestigation
from app.schemas.memory import ProviderStatus, RetainRequest, RetainResponse
from app.services.memory_service import MemoryService, _incident_to_dict
from app.utils.actions import classify_action
from app.utils.logging import get_logger, get_request_id, set_incident_id

log = get_logger("services.agent")


class AgentService:
    """Orchestrates investigation, simulated action, resolution and retention."""

    def __init__(self, session: Session, settings: Optional[Settings] = None) -> None:
        self.session = session
        self.settings = settings or default_settings
        self.incidents = IncidentRepository(session)
        self.investigations = InvestigationRepository(session)
        self.actions = get_action_provider()

    # ------------------------------------------------------------------ util
    def _load(self, incident_id: str) -> Incident:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found",
            )
        set_incident_id(incident_id)
        return incident

    # ---------------------------------------------------------- investigate
    def investigate(
        self,
        incident_id: str,
        *,
        memory_enabled: bool = True,
        extra_context: Optional[str] = None,
    ) -> InvestigationResult:
        """Run the investigation loop for one incident.

        ``memory_enabled=False`` is the honest control condition: the same
        incident, the same signals and the same analysis pipeline, with
        organisational memory withheld. It is not handicapped in any other way.
        """
        started = time.perf_counter()
        incident = self._load(incident_id)

        # --- 1. recall historical experience -------------------------------
        evidence: List[Dict[str, Any]] = []
        memory_status = "disabled"
        memory_source = "none"
        memory_detail: Optional[str] = None
        memory_query: Optional[str] = None
        memory_provider_status: Optional[ProviderStatus] = None

        if memory_enabled:
            memory_service = MemoryService(self.session, self.settings)
            recall_response, evidence, memory_provider_status = memory_service.recall(
                incident, extra_context=extra_context
            )
            memory_query = recall_response.query
            memory_source = recall_response.source
            memory_status = recall_response.status
            memory_detail = recall_response.detail
        else:
            memory_detail = (
                "Organisational memory was disabled for this run (memory OFF control path)."
            )

        # --- 2. analysis ---------------------------------------------------
        incident_dict = _incident_to_dict(incident)
        investigation, llm_status = self._analyse(
            incident=incident_dict,
            evidence=evidence,
            memory_enabled=memory_enabled,
            extra_context=extra_context,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        request_id = get_request_id() or ""

        result = InvestigationResult(
            incident={
                **incident_dict,
                "status": incident.status,
                "deployment_version": incident.deployment_version,
            },
            mode="memory_on" if memory_enabled else "memory_off",
            summary=investigation.summary,
            reasoning_summary=investigation.reasoning_summary
            or "No reasoning summary was produced by the analysis provider.",
            hypotheses=investigation.hypotheses,
            investigation_steps=self._investigation_steps(incident_dict, evidence),
            recommended_action=investigation.recommended_action,
            confidence=self._confidence(investigation, evidence, memory_enabled),
            memory_enabled=memory_enabled,
            memory_count=len(evidence),
            memory_evidence=evidence,
            memory_source=memory_source,
            memory_status=memory_status,
            memory_query=memory_query,
            memory_detail=memory_detail,
            memory_provider=memory_provider_status,
            llm_provider=llm_status,
            limitations=investigation.limitations,
            requires_human_approval=True,
            request_id=request_id,
            duration_ms=duration_ms,
        )

        # --- 3. persist so the run is auditable ----------------------------
        action = result.recommended_action
        self.investigations.create(
            incident_id=incident.id,
            mode=result.mode,
            summary=result.summary,
            reasoning_summary=result.reasoning_summary,
            confidence=result.confidence,
            recommended_action=action.action if action else None,
            action_type=action.action_type if action else None,
            action_risk=action.risk if action else None,
            hypotheses=[h.model_dump() for h in result.hypotheses],
            memory_evidence=evidence,
            memory_count=len(evidence),
            memory_source=memory_source,
            memory_status=memory_status,
            llm_provider=llm_status.name if llm_status else None,
            llm_status=llm_status.mode if llm_status else None,
            limitations=result.limitations,
            request_id=request_id,
            duration_ms=duration_ms,
        )

        # Record that an investigation is under way on the incident itself.
        if incident.status == "active":
            incident.status = "investigating"
            incident.updated_at = utcnow()
            self.incidents.update(incident)

        log.info(
            "investigation complete",
            extra={
                "event_incident_id": incident.id,
                "event_mode": result.mode,
                "event_memory_count": result.memory_count,
                "event_confidence": result.confidence,
                "event_duration_ms": duration_ms,
                "event_llm_provider": llm_status.name if llm_status else None,
            },
        )
        return result

    def _analyse(
        self,
        *,
        incident: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        memory_enabled: bool,
        extra_context: Optional[str],
    ) -> Tuple[LLMInvestigation, Optional[ProviderStatus]]:
        """Produce the structured analysis, degrading cleanly on any failure."""
        provider, fallback, _mode = get_llm_provider(self.settings)
        status_out: Optional[ProviderStatus] = None

        system = self._system_prompt(memory_enabled=memory_enabled)
        user = self._user_prompt(
            incident=incident,
            evidence=evidence,
            memory_enabled=memory_enabled,
            extra_context=extra_context,
        )
        # `memory_enabled` travels in the context so a provider can tell "memory
        # was withheld for the control run" apart from "memory was searched and
        # found nothing". Those are different facts and must never be reported
        # with the same words.
        context: Dict[str, Any] = {
            "incident": incident,
            "memory_evidence": evidence,
            "memory_enabled": memory_enabled,
        }

        outcome = self._call(provider, system, user, context)

        if not outcome.success and fallback is not None:
            log.warning(
                "llm primary failed, using fallback",
                extra={
                    "event_provider": provider.name,
                    "event_error": outcome.detail,
                    "event_fallback": fallback.name,
                },
            )
            outcome = self._call(fallback, system, user, context)
            status_out = ProviderStatus(
                name=fallback.name,
                mode=outcome.mode,
                available=outcome.success,
                detail=(
                    f"{provider.name} unavailable ({outcome.detail or 'failed'}); "
                    f"analysed with the {fallback.name} provider"
                ),
                latency_ms=outcome.latency_ms,
            )
        else:
            status_out = ProviderStatus(
                name=outcome.provider,
                mode=outcome.mode,
                available=outcome.success,
                detail=outcome.detail or f"model={outcome.model}",
                latency_ms=outcome.latency_ms,
            )

        if not outcome.success or not isinstance(outcome.data, dict):
            # Last resort: a minimal valid result rather than a 500.
            log.error(
                "no analysis provider produced a result",
                extra={"event_incident_id": incident.get("id")},
            )
            fallback_result = LLMInvestigation(
                summary=(
                    f"{incident.get('service', 'Service')} is in an active "
                    f"{incident.get('status', 'unknown')} state. Automated analysis "
                    "is unavailable, so no recommendation can be made."
                ),
                reasoning_summary=(
                    "No analysis provider was able to produce a structured "
                    "result for this incident. This is reported rather than hidden."
                ),
                hypotheses=[],
                recommended_action=None,
                limitations=(
                    "Automated analysis unavailable. "
                    + (outcome.detail or "no provider responded")
                ),
                memory_used=[],
            )
            if status_out is None:
                status_out = ProviderStatus(
                    name="none", mode="unavailable", available=False, detail="no provider"
                )
            return fallback_result, status_out

        return LLMInvestigation.model_validate(outcome.data), status_out

    def _call(
        self,
        provider: LLMProvider,
        system: str,
        user: str,
        context: Dict[str, Any],
    ):
        try:
            return provider.complete_json(
                system=system, user=user, schema=LLMInvestigation, context=context
            )
        except Exception as exc:  # noqa: BLE001 - analysis must never 500
            log.warning("llm provider raised", extra={"event_error": type(exc).__name__})
            from app.integrations.base import LLMOutcome

            return LLMOutcome(
                data=None,
                provider=provider.name,
                model=getattr(provider, "model", "unknown"),
                success=False,
                detail=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _system_prompt(*, memory_enabled: bool) -> str:
        base = (
            "You are IncidentMind, an incident response analyst. You reason over "
            "current incident signals and, when available, over resolved incidents "
            "retrieved from this organisation's persistent memory.\n"
            "You never claim to have executed anything; you only recommend. "
            "You never invent metrics, incident ids or historical facts. "
            "You return a single JSON object and no other text. "
            "You do not reveal internal reasoning steps - only a short, factual "
            "summary of your conclusion and the evidence behind it."
        )
        if not memory_enabled:
            base += (
                "\nIMPORTANT: organisational memory is DISABLED for this run. You have "
                "no access to any prior incident. Base your analysis only on the current "
                "incident, state that you have no historical evidence, and keep your "
                "confidence correspondingly low."
            )
        return base

    def _user_prompt(
        self,
        *,
        incident: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        memory_enabled: bool,
        extra_context: Optional[str],
    ) -> str:
        if memory_enabled and evidence:
            memory_block_lines = []
            for item in evidence:
                memory_block_lines.append(
                    "\n".join(
                        [
                            f"[{item.get('source_incident_id') or item.get('memory_id')}]",
                            f"  relevance: {item.get('relevance')} "
                            f"({item.get('relevance_method')}), rank {item.get('rank')}",
                            f"  why relevant: {item.get('why_relevant')}",
                            f"  service: {item.get('historical_service') or 'unknown'}",
                            f"  symptoms: {item.get('historical_symptoms') or 'not recorded'}",
                            f"  root cause: {item.get('historical_root_cause') or 'not recorded'}",
                            f"  action that worked: {item.get('historical_action') or 'not recorded'}",
                            f"  outcome: {item.get('historical_outcome') or 'not recorded'}",
                            f"  lesson: {item.get('historical_lesson') or 'not recorded'}",
                        ]
                    )
                )
            memory_block = "\n".join(memory_block_lines)
        elif memory_enabled:
            memory_block = (
                "  (organisational memory was queried but returned no experience "
                "relevant to this failure pattern)"
            )
        else:
            memory_block = "  (organisational memory is DISABLED for this run)"

        return render(
            "incident_investigation",
            incident_id=incident.get("id", ""),
            incident_title=incident.get("title", ""),
            service=incident.get("service", ""),
            severity=incident.get("severity", ""),
            status=incident.get("status", ""),
            deployment_version=incident.get("deployment_version") or "unknown",
            started_at=incident.get("started_at") or "unknown",
            description=incident.get("description") or "not recorded",
            signals="; ".join(incident.get("signals") or []) or "none recorded",
            metrics=incident.get("metrics") or {},
            memory_count=len(evidence),
            memory_block=memory_block,
        ) + (f"\n\nADDITIONAL OPERATOR CONTEXT: {extra_context}" if extra_context else "")

    @staticmethod
    def _investigation_steps(
        incident: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> List[str]:
        """The auditable list of what was actually done, in order."""
        steps = [
            f"Loaded incident {incident.get('id')} for service {incident.get('service')}.",
            f"Parsed {len(incident.get('signals') or [])} recorded signal(s) and "
            f"{len(incident.get('metrics') or {})} metric(s).",
        ]
        if evidence:
            steps.append(
                f"Recalled {len(evidence)} prior experience(s) from organisational memory."
            )
            for item in evidence:
                steps.append(
                    f"  - {item.get('source_incident_id') or item.get('memory_id')}: "
                    f"{item.get('why_relevant')}"
                )
        else:
            steps.append("No prior experience was available to the analysis.")
        steps.append("Generated ranked failure hypotheses from the assembled evidence.")
        steps.append("Derived a recommended, reversible action for human approval.")
        return steps

    @staticmethod
    def _confidence(
        investigation: LLMInvestigation,
        evidence: List[Dict[str, Any]],
        memory_enabled: bool,
    ) -> float:
        """Overall confidence, from the hypotheses, clamped to 0..1."""
        if not investigation.hypotheses:
            return 0.0
        ranked = sorted(
            investigation.hypotheses, key=lambda h: h.confidence, reverse=True
        )
        return round(min(1.0, max(0.0, ranked[0].confidence)), 4)

    # ------------------------------------------------------------- actions
    def simulate_action(
        self, incident_id: str, request: SimulatedActionRequest
    ) -> SimulatedActionResult:
        """Simulate a human-approved action. Nothing real is executed."""
        incident = self._load(incident_id)

        if not request.approved:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Human approval required. Set 'approved': true to simulate this "
                    "action. IncidentMind never acts without an explicit approval."
                ),
            )

        action_type = request.action_type or self._classify_action(request.action)
        diagnosed = self._diagnosed_action_type(incident_id)

        outcome = self.actions.execute_simulated(
            incident_id=incident.id,
            action=request.action,
            action_type=action_type,
            context={
                "metrics": dict(incident.metrics or {}),
                "diagnosed_action_type": diagnosed,
            },
        )

        log.info(
            "action simulated",
            extra={
                "event_incident_id": incident.id,
                "event_action_type": outcome.action_type,
                "event_success": outcome.success,
                "event_approved_by": request.approved_by,
            },
        )

        return SimulatedActionResult(
            incident_id=incident.id,
            action=request.action,
            action_type=outcome.action_type,
            simulated=True,
            approved_by=request.approved_by,
            success=outcome.success,
            message=outcome.message,
            duration_seconds=outcome.duration_seconds,
            telemetry=[TelemetryPoint(**t) for t in outcome.telemetry],
            notes=outcome.notes,
        )

    @staticmethod
    def _classify_action(action_text: str) -> str:
        """Classify an approved action using the shared action vocabulary.

        Shared with the analyst so a recommended action and a simulated action
        can never be assigned different types.
        """
        return classify_action(action_text)

    def _diagnosed_action_type(self, incident_id: str) -> Optional[str]:
        """The action type the most recent investigation recommended."""
        runs = self.investigations.for_incident(incident_id)
        return runs[0].action_type if runs else None

    # ------------------------------------------------------------- resolve
    def resolve_incident(
        self, incident_id: str, request: ResolveRequest
    ) -> ResolveResponse:
        """Mark an incident resolved and, by default, retain the experience."""
        incident = self._load(incident_id)

        runs = self.investigations.for_incident(incident_id)
        latest = runs[0] if runs else None

        root_cause = request.root_cause or _root_cause_from_hypotheses(latest)
        # Prefer what the operator says was done; fall back to what the agent
        # recommended, so the retained experience always names a real action.
        action_taken = request.action_taken or (latest.recommended_action if latest else None)

        incident.status = "resolved"
        incident.resolved_at = utcnow()
        incident.root_cause = root_cause
        incident.action_taken = action_taken
        incident.failed_action = request.failed_action
        incident.outcome = request.outcome
        incident.lesson = request.lesson or _default_lesson(root_cause, action_taken)
        incident.updated_at = utcnow()

        if request.resolution_time_seconds is not None:
            incident.resolution_time_seconds = request.resolution_time_seconds
        elif incident.started_at:
            incident.resolution_time_seconds = round(
                (incident.resolved_at - incident.started_at).total_seconds(), 1
            )
        self.incidents.update(incident)

        response = ResolveResponse(
            incident_id=incident.id,
            status=incident.status,
            outcome=incident.outcome or "resolved",
            resolution_time_seconds=incident.resolution_time_seconds,
        )

        if request.retain:
            # Retention is a follow-up effect, not part of resolving the
            # incident. If it cannot happen (no root cause recorded, memory
            # service down) the resolution still stands and the response says
            # so, rather than failing the whole request.
            try:
                retain_response = self.retain_incident(incident_id)
                response.retained = retain_response.success
                response.retain_status = retain_response.status
                response.memory_event_id = retain_response.memory_event_id
            except HTTPException as exc:
                response.retained = False
                response.retain_status = "failed"
                log.warning(
                    "retention after resolution did not complete",
                    extra={
                        "event_incident_id": incident.id,
                        "event_reason": str(exc.detail),
                    },
                )

        log.info(
            "incident resolved",
            extra={
                "event_incident_id": incident.id,
                "event_retained": response.retained,
            },
        )
        return response

    # -------------------------------------------------------------- retain
    def retain_incident(self, incident_id: str) -> RetainResponse:
        """Retain the resolved experience of an incident to memory."""
        incident = self._load(incident_id)
        runs = self.investigations.for_incident(incident_id)
        latest = runs[0] if runs else None

        if not incident.root_cause:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Incident '{incident_id}' has no recorded root cause. Resolve it "
                    "with a root cause before retaining it to memory."
                ),
            )

        request = RetainRequest(
            incident_id=incident.id,
            service=incident.service,
            symptoms=incident.description,
            signals=list(incident.signals or []),
            metrics=dict(incident.metrics or {}),
            deployment=incident.deployment_version or incident.recent_change,
            investigation=[r.summary for r in runs[:5] if r.summary],
            root_cause=incident.root_cause,
            actions_tried=[r.recommended_action for r in runs if r.recommended_action],
            successful_action=incident.action_taken,
            failed_action=incident.failed_action,
            outcome=incident.outcome or "resolved",
            resolution_time=(
                f"{incident.resolution_time_seconds} seconds"
                if incident.resolution_time_seconds is not None
                else None
            ),
            lesson=incident.lesson or _default_lesson(incident.root_cause, incident.action_taken),
        )

        memory_service = MemoryService(self.session, self.settings)
        return memory_service.retain(incident, request)

    # -------------------------------------------------------------- history
    def history(self, incident_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        runs = (
            self.investigations.for_incident(incident_id)
            if incident_id
            else self.investigations.all(limit=limit)
        )
        return [
            {
                "id": r.id,
                "incident_id": r.incident_id,
                "mode": r.mode,
                "summary": r.summary,
                "confidence": r.confidence,
                "recommended_action": r.recommended_action,
                "memory_count": r.memory_count,
                "memory_source": r.memory_source,
                "llm_provider": r.llm_provider,
                "created_at": r.created_at,
            }
            for r in runs[:limit]
        ]


def _root_cause_from_hypotheses(run) -> Optional[str]:
    """Take the highest-confidence hypothesis as the root cause, if any."""
    if run is None or not run.hypotheses:
        return None
    best = max(run.hypotheses, key=lambda h: float(h.get("confidence", 0)))
    return best.get("cause")


def _default_lesson(root_cause: Optional[str], action: Optional[str]) -> str:
    if root_cause and action:
        return (
            f"When this failure shape appears again, check for the same root cause "
            f"({root_cause}) before exploring new options. The remedy that worked was: {action}."
        )
    if root_cause:
        return f"Recurring failure shape with root cause: {root_cause}. Investigate this first."
    return "Capture a concrete root cause and remedy so this incident is reusable."
