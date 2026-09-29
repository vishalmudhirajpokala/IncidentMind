"""Deterministic LLM provider (DEMO / offline path).

This is not a placeholder that returns canned text. It is a rule-based analyst
that reads the same structured evidence the live model receives and produces a
genuine, reproducible analysis. It is what makes the demo reliable when the
Groq API is unreachable.

Honesty rules baked in here:

  * It never claims to be an LLM. ``mode`` is reported as ``demo``.
  * With memory evidence it cites the historical incident id, root cause, action
    and outcome, and raises confidence accordingly.
  * With no memory evidence it says so and keeps confidence low. It does not
    invent history to look more capable.
  * It applies no penalty to the memory-OFF path beyond the honest consequence
    of having no evidence to reason from.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.integrations.base import LLMOutcome, LLMProvider
from app.integrations.relevance import FAILURE_PATTERN_TERMS, tokenize
from app.schemas.agent import Hypothesis, RecommendedAction
from app.schemas.llm import LLMInvestigation
from app.schemas.memory import ProviderStatus
from app.utils.actions import classify_action, extract_target_version, to_present_tense
from app.utils.logging import get_logger

log = get_logger("integrations.deterministic")

_VERSION_RE = re.compile(r"v?\d+\.\d+(?:\.\d+)?")

# Failure-shape rules, most specific first. The first rule whose ``match`` set
# intersects the incident tokens wins, so ordering encodes specificity:
# a "connection pool exhausted" report is a pool problem even when it also
# mentions latency and 503s.
PATTERN_RULES: List[Dict[str, Any]] = [
    {
        "id": "db_pool",
        "match": {"pool", "connection", "connections", "pooling", "exhausted", "exhaustion"},
        "cause": "Database connection pool exhaustion under load",
        "action_type": "connection_pool",
        "investigate": "Check pool saturation and long-held connections",
    },
    {
        "id": "memory_pressure",
        "match": {"memory", "oom", "leak", "heap", "rss"},
        "cause": "Memory pressure or a leak in the service",
        "action_type": "restart",
        "investigate": "Inspect heap usage and allocation rate",
    },
    {
        "id": "latency",
        "match": {"latency", "slow", "degraded", "p99", "p95", "tail"},
        "cause": "Latency regression in a downstream dependency",
        "action_type": "scale",
        "investigate": "Profile downstream dependency latency and saturation",
    },
    {
        "id": "capacity",
        "match": {"cpu", "disk", "saturation", "overload", "throttle", "throttling"},
        "cause": "Resource saturation on the serving tier",
        "action_type": "scale",
        "investigate": "Check host and container resource saturation",
    },
    {
        "id": "dependency",
        "match": {"timeout", "timeouts", "failover", "replication", "unavailable", "cascade"},
        "cause": "Downstream dependency failure or timeout cascade",
        "action_type": "traffic_shift",
        "investigate": "Check downstream dependency health and error budget",
    },
    {
        "id": "deployment_regression",
        "match": {"503", "502", "500", "regression", "deploy", "deployment"},
        "cause": "Regression introduced by the most recent deployment",
        "action_type": "rollback",
        "investigate": "Compare the current release against the previous one",
    },
]


def classify_pattern(incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Identify the failure shape of the current incident."""
    text = " ".join(
        filter(
            None,
            [
                incident.get("description") or "",
                incident.get("title") or "",
                " ".join(incident.get("signals") or []),
                " ".join(str(v) for v in (incident.get("metrics") or {}).values()),
            ],
        )
    )
    tokens = tokenize(text)
    for rule in PATTERN_RULES:
        if tokens & rule["match"]:
            return rule
    return None


def _extract_target_version(historical_action: str) -> Optional[str]:
    """Pull the 'good' version out of a historical action string."""
    lowered = historical_action.lower()
    for marker in (" to ", "->", "→"):
        if marker in lowered:
            tail = lowered.split(marker)[-1]
            match = _VERSION_RE.search(tail)
            if match:
                return match.group(0)
    versions = _VERSION_RE.findall(historical_action)
    return versions[-1] if len(versions) > 1 else None


def _build_action(
    *,
    incident: Dict[str, Any],
    evidence: Dict[str, Any],
    pattern: Optional[Dict[str, Any]],
) -> RecommendedAction:
    """Derive the recommended action, preferring historical experience."""
    service = incident.get("service") or "the service"
    current_version = incident.get("deployment_version")
    historical_action = (evidence.get("historical_action") or "").strip()
    historical_root_cause = (evidence.get("historical_root_cause") or "").strip()
    historical_id = evidence.get("source_incident_id") or "a prior incident"

    if historical_action:
        # The action type describes the action, not the diagnosis, so it is
        # derived from the historical action text itself.
        action_type = _classify_action(historical_action)
        if action_type == "rollback":
            target = _extract_target_version(historical_action)
            if target:
                action = (
                    f"Rollback {service} from {current_version or 'the current release'} "
                    f"to the last known-good release ({target}, per {historical_id})"
                )
            else:
                action = (
                    f"Rollback {service} from {current_version or 'the current release'} "
                    f"to the last known-good release, as in {historical_id}"
                )
            reason = (
                f"{historical_id} presented the same failure pattern and was resolved by "
                f"'{historical_action}'. Applying the same remedy here rather than "
                "proposing an untested one."
            )
        else:
            action = _to_present_tense(historical_action)
            reason = (
                f"{historical_id} hit the same failure pattern (root cause: "
                f"{historical_root_cause or 'similar'}) and this action resolved it. "
                f"Reapplying the recorded remedy rather than proposing an untested one."
            )
        return RecommendedAction(
            action=action,
            reason=reason,
            risk="medium",
            action_type=action_type,
        )

    # ---- No historical experience -------------------------------------
    # A rollback is the safest reversible first move whenever a release is the
    # most plausible trigger: it is fast, reversible, and does not add a second
    # variable while the incident is still open. It is proposed only for
    # failure shapes a code change can plausibly cause, and only when a
    # deployment is actually on record.
    _CODE_CAUSED = {"db_pool", "deployment_regression", "memory_pressure", "latency"}
    if current_version and pattern and pattern["id"] in _CODE_CAUSED:
        return RecommendedAction(
            action=(
                f"Rollback {service} from {current_version} to the previous "
                "known-good release"
            ),
            reason=(
                f"Symptoms began after {current_version} was deployed and the failure shape "
                f"({pattern['id']}) is one a code change can cause. No prior incident in "
                "organisational memory matches this pattern, so the safest reversible step "
                "is a rollback while the change is investigated."
            ),
            risk="medium",
            action_type="rollback",
        )
    if pattern and pattern["id"] == "capacity":
        return RecommendedAction(
            action=f"Increase capacity for {service} and re-check saturation",
            reason="Observed resource saturation. No matching prior incident is on record.",
            risk="low",
            action_type="scale",
        )
    if pattern and pattern["id"] == "memory_pressure":
        return RecommendedAction(
            action=f"Restart {service} to reclaim memory, then profile heap usage",
            reason="Observed memory pressure. No matching prior incident is on record.",
            risk="medium",
            action_type="restart",
        )
    if pattern and pattern["id"] == "db_pool":
        return RecommendedAction(
            action=f"Check connection pool saturation and long-held connections on {service}",
            reason=(
                "Signals indicate connection pool exhaustion, but no deployment is on "
                "record. No prior incident in organisational memory matches this pattern, "
                "so start with pool telemetry."
            ),
            risk="low",
            action_type="connection_pool",
        )
    if pattern and pattern["id"] == "dependency":
        return RecommendedAction(
            action=f"Check {service} downstream dependency health and error budget",
            reason=(
                "Signals indicate a dependency timeout. No matching prior incident is on "
                "record, so the dependency is the right place to look first."
            ),
            risk="low",
            action_type="traffic_shift",
        )
    return RecommendedAction(
        action=f"Investigate {service} signals and recent changes before acting",
        reason=(
            "Insufficient signal detail to propose a specific remedy, and no matching "
            "prior incident exists in organisational memory."
        ),
        risk="low",
        action_type="investigate",
    )


def _classify_action(action_text: str) -> str:
    return classify_action(action_text)


def _to_present_tense(action_text: str) -> str:
    return to_present_tense(action_text)


def _sentence(value: Optional[str]) -> Optional[str]:
    """Normalise a remembered fact to a single readable phrase.

    Retained facts are assembled from labelled parts, so a field can arrive with
    stray newlines or trailing punctuation. It is quoted mid-sentence, so the
    text is tidied but no terminal punctuation is added - the calling template
    owns that and would otherwise produce a doubled full stop.
    """
    if not value:
        return value
    return " ".join(str(value).split()).strip().rstrip(".;:,")


def _extract_target_version(historical_action: str) -> Optional[str]:
    return extract_target_version(historical_action)


class DeterministicLLMProvider(LLMProvider):
    """Rule-based analyst used in demo mode and as a live-path fallback."""

    name = "deterministic"
    model = "rule-based-analyst-v1"

    def is_configured(self) -> bool:
        return True

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: Type[BaseModel],
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMOutcome:
        started = time.perf_counter()
        context = context or {}
        incident: Dict[str, Any] = context.get("incident") or {}
        evidence: List[Dict[str, Any]] = context.get("memory_evidence") or []

        pattern = classify_pattern(incident)
        service = incident.get("service") or "the service"
        deployment = incident.get("deployment_version") or "an unidentified release"

        hypotheses: List[Hypothesis] = []
        current_signals = [
            f"Current signals: {', '.join(incident.get('signals') or []) or 'none recorded'}"
        ]

        # --- hypothesis 1: what the current evidence alone suggests ---------
        hypotheses.append(
            Hypothesis(
                cause=pattern["cause"] if pattern else "Cause not yet determined from current signals",
                confidence=0.35 if pattern else 0.2,
                evidence=[f"Classified failure shape: {pattern['id']}" if pattern else "No dominant signal pattern"] + current_signals,
            )
        )

        memory_used: List[str] = []
        recommended: RecommendedAction
        limitations: Optional[str]

        if evidence:
            primary = evidence[0]
            historical_id = primary.get("source_incident_id") or "a prior incident"
            memory_used = [
                e.get("source_incident_id")
                for e in evidence
                if e.get("source_incident_id")
            ]

            hypotheses.insert(
                0,
                Hypothesis(
                    cause=(
                        f"Recurrence of the failure pattern seen in {historical_id}"
                        f" ({primary.get('historical_root_cause') or 'root cause not recorded'})"
                    ),
                    # Confidence is driven by the locally computed relevance and
                    # by how many independent memories agree. Never hard-coded high.
                    confidence=round(
                        min(0.95, 0.55 + 0.35 * float(primary.get("relevance") or 0.0)),
                        3,
                    ),
                    evidence=[
                        f"{historical_id}: {primary.get('why_relevant') or 'retrieved from organisational memory'}",
                        f"Historical root cause: {primary.get('historical_root_cause') or 'not recorded'}",
                        f"Historical action that worked: {primary.get('historical_action') or 'not recorded'}",
                        f"Historical outcome: {primary.get('historical_outcome') or 'not recorded'}",
                    ],
                ),
            )

            recommended = _build_action(incident=incident, evidence=primary, pattern=pattern)
            limitations = (
                f"Based on {len(evidence)} recalled experience(s); "
                "the historical remedy may need adjustment for the current scale or release."
            )
        else:
            recommended = _build_action(incident=incident, evidence={}, pattern=pattern)
            # "Searched and found nothing" and "never searched" are different
            # facts. Claiming memory is empty when it was merely withheld would
            # misrepresent the control run as a real absence of experience.
            if (context or {}).get("memory_enabled", True):
                limitations = (
                    "Organisational memory was searched and returned nothing relevant to this "
                    "incident. This recommendation is derived from current incident signals only."
                )
            else:
                limitations = (
                    "Organisational memory was withheld for this run (the memory-OFF control "
                    "path), not found empty. This recommendation is derived from current "
                    "incident signals alone; run the same incident with memory enabled to see "
                    "what history would add."
                )

        # --- summaries ------------------------------------------------------
        # "shows <cause>" rather than "is <cause>": the cause is a condition
        # being observed, not an identity.
        condition = (pattern["cause"][0].lower() + pattern["cause"][1:]) if pattern else "failing"
        if evidence:
            primary = evidence[0]
            historical_id = primary.get("source_incident_id") or "a prior incident"
            summary = (
                f"{service} shows {condition} on {deployment}. Organisational memory holds a "
                f"matching experience from {historical_id}, which was resolved by: "
                f"{_sentence(primary.get('historical_action')) or 'an unrecorded action'}."
            )
            reasoning_summary = (
                f"Retrieved {len(evidence)} prior experience(s) from organisational memory. "
                f"The closest is {historical_id} (relevance "
                f"{primary.get('relevance')}), matched because: "
                f"{_sentence(primary.get('why_relevant')) or 'failure pattern overlap'}. "
                f"Its recorded root cause was "
                f"{_sentence(primary.get('historical_root_cause')) or 'not recorded'}. "
                f"The recorded outcome was "
                f"{_sentence(primary.get('historical_outcome')) or 'not recorded'}. "
                "The recommendation reuses that remedy rather than proposing an untested one."
            )
        elif (context or {}).get("memory_enabled", True):
            summary = (
                f"{service} shows {condition} on {deployment}. "
                "No matching prior incident is on record."
            )
            reasoning_summary = (
                "Memory recall returned no experience relevant to this failure pattern, so the "
                "analysis rests on the current incident signals only. Confidence is therefore "
                "low and the recommended step is the safest reversible option available."
            )
        else:
            summary = (
                f"{service} shows {condition} on {deployment}. "
                "This run was analysed without consulting organisational memory."
            )
            reasoning_summary = (
                "Memory was withheld for this run rather than searched, so no history informed "
                "this analysis. The recommendation below comes from the current incident signals "
                "alone and is therefore generic. Run the same incident with memory enabled to "
                "compare."
            )

        result = LLMInvestigation(
            summary=summary,
            reasoning_summary=reasoning_summary,
            hypotheses=hypotheses,
            recommended_action=recommended,
            limitations=limitations,
            memory_used=memory_used,
        )

        log.info(
            "deterministic analysis complete",
            extra={
                "event_memory_count": len(evidence),
                "event_pattern": pattern["id"] if pattern else "unclassified",
            },
        )

        return LLMOutcome(
            data=result.model_dump(),
            provider=self.name,
            model=self.model,
            success=True,
            mode="demo",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def health(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            mode="demo",
            available=True,
            detail="deterministic rule-based analyst (no external calls)",
        )
