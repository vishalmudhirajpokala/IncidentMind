"""Memory service: query construction, recall with graceful degradation, and
structured experience retention.

Responsibilities
  * Build a rich, specific recall query from the live incident. Never a generic
    "how do I fix this".
  * Try the primary memory provider, fall back cleanly, and always report which
    provider actually answered and whether the result was degraded.
  * Retain a structured experience record - not a log dump, and scrubbed of
    anything secret-shaped before it leaves the process.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import Session
from pydantic import BaseModel

from app.config import Settings, settings as default_settings
from app.integrations.base import MemoryProvider, RetrievedMemory, RetainOutcome
from app.integrations.factory import get_memory_provider, get_llm_provider
from app.integrations.local_memory_provider import LocalMemoryProvider
from app.integrations.relevance import (
    QueryProfile,
    contains_secret_like,
    explain,
    score_relevance,
    tokenize,
)
from app.models.incident import Incident
from app.prompts import render
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import (
    MemoryEvidence,
    MemoryEventRead,
    MemoryRecallResponse,
    ProviderStatus,
    RetainRequest,
    RetainResponse,
)
from app.utils.logging import get_logger

log = get_logger("services.memory")

# Fields of an experience that are written to memory as individually labelled
# items so they can be reconstructed after Hindsight's fact extraction.
_EXPERIENCE_FIELDS = [
    ("symptoms", "SYMPTOMS"),
    ("signals", "KEY SIGNALS"),
    ("metrics", "METRICS AT FAILURE"),
    ("deployment", "TRIGGERING CHANGE"),
    ("investigation", "INVESTIGATION PERFORMED"),
    ("root_cause", "ROOT CAUSE"),
    ("actions_tried", "ACTIONS ATTEMPTED"),
    ("successful_action", "ACTION THAT RESOLVED IT"),
    ("failed_action", "ACTION THAT DID NOT WORK"),
    ("outcome", "OUTCOME"),
    ("resolution_time", "RESOLUTION TIME"),
    ("lesson", "LESSON LEARNED"),
]


def build_recall_query(incident: Incident, extra_context: Optional[str] = None) -> str:
    """Compose a specific multi-facet recall query for the live incident.

    Facets mirror the retrieval vocabulary: which service, what it looks like,
    what the signals said, what changed, what else is going on, and the failure
    pattern itself.
    """
    lines: List[str] = []

    service = incident.service or "unknown service"
    lines.append(f"SERVICE: {service}")

    if incident.title:
        lines.append(f"INCIDENT: {incident.title}")
    if incident.description:
        lines.append(f"SYMPTOMS: {incident.description.strip()}")
    if incident.signals:
        lines.append("SIGNALS: " + "; ".join(str(s) for s in incident.signals))
    if incident.metrics:
        metrics = ", ".join(f"{k}={v}" for k, v in incident.metrics.items())
        lines.append(f"METRICS: {metrics}")
    if incident.deployment_version:
        lines.append(f"CHANGE: deployed {incident.deployment_version}")
    if incident.recent_change:
        lines.append(f"CHANGE: {incident.recent_change}")
    lines.append(f"CONTEXT: severity={incident.severity}, status={incident.status}")

    profile = QueryProfile.from_incident(_incident_to_dict(incident))
    if profile.pattern_tokens:
        lines.append("FAILURE PATTERN: " + ", ".join(sorted(profile.pattern_tokens)))
    if profile.version_family:
        lines.append(f"RELEASE LINE: {profile.version_family}.x")

    if extra_context:
        lines.append(f"ADDITIONAL CONTEXT: {extra_context.strip()}")

    lines.append(
        "Find resolved incidents in organisational memory with the same service, "
        "similar symptoms, the same failure pattern and a comparable triggering change. "
        "Return what the root cause was, which action resolved it, and the outcome."
    )
    return "\n".join(lines)


def _incident_to_dict(incident: Incident) -> Dict[str, Any]:
    return {
        "id": incident.id,
        "title": incident.title,
        "service": incident.service,
        "severity": incident.severity,
        "status": incident.status,
        "description": incident.description,
        "signals": list(incident.signals or []),
        "metrics": dict(incident.metrics or {}),
        "deployment_version": incident.deployment_version,
        "recent_change": incident.recent_change,
    }


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    if isinstance(value, dict):
        return [f"{k}={v}" for k, v in value.items()]
    return [str(value)]


def _scrub(text: str) -> str:
    """Remove anything that looks like a credential before it is stored."""
    if not text:
        return ""
    cleaned = text
    patterns = [
        r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[=:]\s*\S+",
        r"(?i)authorization:\s*\S+",
        r"(?i)bearer\s+[A-Za-z0-9._\-]+",
        r"(?i)\b(?:postgres|postgresql|mysql|mongodb|redis)://\S+",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "[redacted]", cleaned)
    return cleaned


class MemoryService:
    """All organisational-memory operations."""

    def __init__(
        self,
        session: Session,
        settings: Optional[Settings] = None,
    ) -> None:
        self.session = session
        self.settings = settings or default_settings
        self.repo = MemoryRepository(session)
        self.provider, self.fallback, self.mode = get_memory_provider(session, self.settings)

    # ---------------------------------------------------------------- recall
    def recall(
        self,
        incident: Incident,
        *,
        limit: Optional[int] = None,
        extra_context: Optional[str] = None,
    ) -> Tuple[MemoryRecallResponse, List[Dict[str, Any]], ProviderStatus]:
        """Recall historical experience for an incident.

        Returns ``(response, evidence_as_dicts, provider_status)``. The dicts
        are what the LLM layer consumes as structured context.
        """
        limit = limit or self.settings.MEMORY_RECALL_LIMIT
        query = build_recall_query(incident, extra_context)
        incident_dict = _incident_to_dict(incident)

        primary_result: List[RetrievedMemory] = []
        detail: Optional[str] = None
        source = self.provider.name
        degraded = False

        try:
            primary_result = self._provider_recall(self.provider, query, limit, incident_dict)
        except Exception as exc:  # noqa: BLE001 - recall must never break a request
            log.warning("memory recall failed", extra={"event_error": type(exc).__name__})
            detail = f"{type(exc).__name__}: {exc}"

        if not primary_result and self.fallback is not None:
            degraded = True
            try:
                primary_result = self._provider_recall(self.fallback, query, limit, incident_dict)
                source = self.fallback.name
                detail = detail or "primary memory provider returned nothing; used the local mirror"
            except Exception as exc:  # noqa: BLE001
                log.warning("memory fallback failed", extra={"event_error": type(exc).__name__})
                detail = f"fallback failed: {type(exc).__name__}"

        evidence = [
            self._to_evidence(memory, index, incident_dict)
            for index, memory in enumerate(primary_result)
        ]

        response = MemoryRecallResponse(
            query=query,
            memories=evidence,
            count=len(evidence),
            source=source if evidence else "none",
            status="degraded" if degraded and evidence else ("ok" if evidence else "empty"),
            detail=detail,
        )

        status = self.provider.health()
        if degraded and evidence:
            status = ProviderStatus(
                name=source,
                mode="demo" if source == "local" else status.mode,
                available=True,
                detail=detail or "served by fallback provider",
            )

        log.info(
            "memory recall complete",
            extra={
                "event_incident_id": incident.id,
                "event_count": len(evidence),
                "event_source": response.source,
                "event_status": response.status,
            },
        )
        return response, [e.model_dump() for e in evidence], status

    def _provider_recall(
        self,
        provider: MemoryProvider,
        query: str,
        limit: int,
        incident_dict: Dict[str, Any],
    ) -> List[RetrievedMemory]:
        """Call a provider, passing incident context when it understands it."""
        if isinstance(provider, LocalMemoryProvider):
            return provider.recall(query, limit=limit, incident=incident_dict)
        return provider.recall(query, limit=limit)

    def _to_evidence(
        self,
        memory: RetrievedMemory,
        index: int,
        incident_dict: Dict[str, Any],
    ) -> MemoryEvidence:
        """Map a raw provider record onto the public evidence schema.

        Hindsight returns extracted *facts*, not a structured record, so the
        historical fields are recovered from the labelled ``context`` marker and
        the fact text. When they cannot be recovered the fields stay ``None``
        rather than being guessed.
        """
        raw = memory.raw or {}
        metadata: Dict[str, Any] = dict(raw.get("metadata") or {})

        if not metadata and memory.provider != "local":
            metadata = self._parse_fact_text(memory.text, memory.context)

        source_incident_id = (
            metadata.get("incident_id")
            or raw.get("source_incident_id")
            or self._incident_id_from_context(memory.context)
            or (memory.entities[0] if memory.entities and memory.entities[0].startswith("INC-") else None)
        )

        # Relevance: prefer a score the provider actually returned. Hindsight
        # returns none, so the documented local lexical score is used and is
        # always labelled as locally computed - never attributed to Hindsight.
        if memory.score is not None and memory.provider != "local":
            relevance = round(float(memory.score), 4)
            method = f"{memory.provider}_reported_score"
        else:
            profile = QueryProfile.from_incident(incident_dict)
            merged = {**metadata, "content": memory.text, "title": memory.context}
            relevance_result = score_relevance(profile, merged)
            relevance = relevance_result.score
            method = relevance_result.method
            raw.setdefault("matched_on", relevance_result.matched_on)

        matched_on = list(raw.get("matched_on") or [])
        if not matched_on and relevance > 0:
            matched_on = ["retrieved by the memory provider for this query"]

        return MemoryEvidence(
            memory_id=memory.id,
            source_incident_id=source_incident_id,
            historical_title=metadata.get("title") or memory.context,
            historical_service=metadata.get("service"),
            historical_symptoms=metadata.get("symptoms"),
            historical_root_cause=metadata.get("root_cause"),
            historical_action=metadata.get("successful_action") or metadata.get("action_taken"),
            historical_outcome=metadata.get("outcome"),
            historical_lesson=metadata.get("lesson"),
            why_relevant=str(raw.get("why_relevant") or explain(matched_on)),
            matched_on=matched_on,
            rank=index + 1,
            relevance=relevance,
            relevance_method=method,
            provider=memory.provider,
            text=memory.text,
        )

    @staticmethod
    def _incident_id_from_context(context: Optional[str]) -> Optional[str]:
        if not context:
            return None
        match = re.search(r"(INC-\d+)", context)
        return match.group(1) if match else None

    @staticmethod
    def _parse_fact_text(text: str, context: Optional[str]) -> Dict[str, Any]:
        """Recover structured fields from a ``LABEL: value`` fact string."""
        fields: Dict[str, Any] = {}
        if not text:
            return fields
        for line in text.splitlines():
            if ":" not in line:
                continue
            label, _, value = line.partition(":")
            label_key = label.strip().lower().replace(" ", "_")
            if label_key and value.strip():
                fields[label_key] = value.strip()
        if context:
            fields.setdefault("title", context)
        return fields

    # ---------------------------------------------------------------- retain
    def build_experience_items(
        self, incident: Incident, request: RetainRequest
    ) -> List[Dict[str, Any]]:
        """Build the labelled items that make up one retained experience.

        Each item is a single self-describing line so that, after Hindsight's
        fact extraction, every part is still interpretable on the way back.
        """
        context_marker = f"incident:{request.incident_id} | service:{request.service or incident.service}"
        items: List[Dict[str, Any]] = [
            {
                "label": "title",
                "title": incident.title,
                "content": _scrub(f"INCIDENT {request.incident_id}: {incident.title}"),
                "context": context_marker,
                "tags": [
                    f"incident:{request.incident_id}",
                    f"service:{request.service or incident.service}",
                    "kind:incident_experience",
                ],
            }
        ]

        values: Dict[str, Any] = {
            "service": request.service or incident.service,
            "symptoms": request.symptoms or incident.description,
            "signals": request.signals or list(incident.signals or []),
            "metrics": request.metrics or dict(incident.metrics or {}),
            "deployment": request.deployment or incident.deployment_version,
            "investigation": request.investigation,
            "root_cause": request.root_cause,
            "actions_tried": request.actions_tried,
            "successful_action": request.successful_action,
            "failed_action": request.failed_action,
            "outcome": request.outcome,
            "resolution_time": request.resolution_time,
            "lesson": request.lesson,
        }

        for key, label in _EXPERIENCE_FIELDS:
            value = values.get(key)
            rendered = _render_field(value)
            if not rendered or rendered.lower() in {"unknown", "none", "n/a"}:
                continue
            items.append(
                {
                    "label": key,
                    "content": _scrub(f"{label}: {rendered}"),
                    "context": context_marker,
                }
            )

        return items

    def build_narrative(
        self,
        incident: Incident,
        request: RetainRequest,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Compose the prose memory entry for this experience.

        Uses the live LLM when one is configured and falls back to a
        deterministic composer. The deterministic composer is the demo default
        so that a retained experience is always well-formed offline.
        """
        if items is None:
            items = self.build_experience_items(incident, request)
        deterministic = "\n".join(item["content"] for item in items)

        provider, _fallback, _mode = get_llm_provider(self.settings)
        if not provider.is_configured() or provider.name == "deterministic":
            return deterministic

        try:
            system = (
                "You write durable organisational memory entries from resolved incident facts. "
                "Return a single JSON object with one key: 'entry' containing the prose memory "
                "text. Never include secrets or raw logs."
            )
            user = render(
                "memory_retain",
                incident_id=request.incident_id,
                service=values_for_prompt(request, "service"),
                symptoms=values_for_prompt(request, "symptoms"),
                signals=values_for_prompt(request, "signals"),
                deployment=values_for_prompt(request, "deployment"),
                investigation=values_for_prompt(request, "investigation"),
                root_cause=values_for_prompt(request, "root_cause"),
                actions_tried=values_for_prompt(request, "actions_tried"),
                successful_action=values_for_prompt(request, "successful_action"),
                failed_action=values_for_prompt(request, "failed_action"),
                outcome=values_for_prompt(request, "outcome"),
                resolution_time=values_for_prompt(request, "resolution_time"),
                lesson=values_for_prompt(request, "lesson"),
            )
            outcome = provider.complete_json(
                system=system,
                user=user,
                schema=_RetainEntry,
                context={"incident": _incident_to_dict(incident), "experience": request.model_dump()},
            )
            if outcome.success and isinstance(outcome.data, dict):
                entry = outcome.data.get("entry")
                if entry and not contains_secret_like(str(entry)):
                    return str(entry)
        except Exception as exc:  # noqa: BLE001
            log.warning("narrative generation failed", extra={"event_error": type(exc).__name__})

        return deterministic

    def retain(
        self, incident: Incident, request: RetainRequest
    ) -> RetainResponse:
        """Retain a resolved experience and keep a local record of it.

        When the primary provider is external, a local mirror row is always
        written so the demo, the history view and the metrics endpoint keep
        working with or without the external service. When the primary provider
        *is* the local store, it has already written the row and nothing is
        written twice. The response states which of the two happened.
        """
        # --- the structured experience record, scrubbed --------------------
        # This is the authoritative shape of what is being remembered. It is
        # attached to the items so whichever provider is active can store it
        # verbatim; the external adapter ignores it and sends only content.
        metadata = {
            "incident_id": request.incident_id,
            "title": _scrub(incident.title),
            "service": request.service or incident.service,
            "symptoms": _scrub(request.symptoms or incident.description or ""),
            "signals": [_scrub(s) for s in _coerce_list(request.signals)],
            "metrics": request.metrics or dict(incident.metrics or {}),
            "deployment": request.deployment or incident.deployment_version,
            "investigation": [_scrub(s) for s in _coerce_list(request.investigation)],
            "root_cause": _scrub(request.root_cause),
            "actions_tried": [_scrub(s) for s in _coerce_list(request.actions_tried)],
            "successful_action": _scrub(request.successful_action or ""),
            "failed_action": _scrub(request.failed_action or ""),
            "outcome": _scrub(request.outcome),
            "resolution_time": request.resolution_time,
            "lesson": _scrub(request.lesson),
        }

        items = self.build_experience_items(incident, request)
        content = self.build_narrative(incident, request, items=items)
        for item in items:
            item["metadata"] = metadata
            item["narrative"] = content

        # --- primary provider ----------------------------------------------
        external = RetainOutcome(
            success=False,
            provider=self.provider.name,
            external=False,
            detail="memory provider not configured",
        )
        try:
            external = self.provider.retain_batch(items, document_id=request.incident_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("retain to provider failed", extra={"event_error": type(exc).__name__})
            external = RetainOutcome(
                success=False,
                provider=self.provider.name,
                external=False,
                detail=f"{type(exc).__name__}: {exc}",
            )

        provider_is_local = self.provider.name == "local"
        if provider_is_local:
            # The local provider already persisted the record with this exact
            # metadata. Adopt that row rather than writing a duplicate.
            event = next(
                (
                    found
                    for found in self.repo.for_incident(request.incident_id)
                    if found.id in (external.external_ids or [])
                ),
                None,
            )
            if event is None:
                stored = self.repo.for_incident(request.incident_id)
                event = stored[0] if stored else self.repo.create(
                    incident_id=request.incident_id,
                    event_type="experience",
                    title=metadata["title"],
                    symptoms=metadata["symptoms"],
                    content=content,
                    metadata=metadata,
                    provider=self.provider.name,
                    external_retained=False,
                )
        else:
            event = self.repo.create(
                incident_id=request.incident_id,
                event_type="experience",
                title=metadata["title"],
                symptoms=metadata["symptoms"],
                content=content,
                metadata=metadata,
                provider=self.provider.name,
                external_retained=external.success and external.external,
                external_ids=external.external_ids,
                external_error=None if external.success else external.detail,
            )

        log.info(
            "experience retained",
            extra={
                "event_incident_id": request.incident_id,
                "event_provider": self.provider.name,
                "event_external": event.external_retained,
            },
        )

        if event.external_retained:
            status: str = "retained"
        else:
            status = "retained_locally"

        return RetainResponse(
            incident_id=request.incident_id,
            success=True,
            memory_event_id=event.id,
            provider=self.provider.name,
            external_retained=event.external_retained,
            status=status,  # type: ignore[arg-type]
            detail=external.detail or "Stored in the local memory mirror",
            external_ids=event.external_ids,
        )

    # ----------------------------------------------------------------- read
    def recent(self, limit: int = 20, incident_id: Optional[str] = None) -> List[MemoryEventRead]:
        if incident_id:
            events = self.repo.for_incident(incident_id)
        else:
            events = self.repo.most_recent(limit=limit)
        return [MemoryEventRead.model_validate(e) for e in events]

    def health(self) -> ProviderStatus:
        return self.provider.health()


def _render_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v not in (None, ""))
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def values_for_prompt(request: RetainRequest, key: str) -> str:
    return _render_field(getattr(request, key, None)) or "unknown"


class _RetainEntry(BaseModel):
    """Schema for the LLM-authored memory entry."""

    entry: str


__all__ = [
    "MemoryService",
    "build_recall_query",
    "RetainOutcome",
    "tokenize",
]
