"""The deterministic learning-loop demo.

The scenario is the whole point of the project, so it is scripted end to end
and asserted by the API itself, not left to narration:

    1. A new incident (A) is investigated with memory ON. It is the first
       checkout-api pool incident this deployment has retained, so recall should
       be empty and the recommendation should be generic.
    2. A is resolved and its experience retained to organisational memory.
    3. A second incident (B) arrives for the same service and the same failure
       pattern, described in completely different words.
    4. B is investigated twice: once with memory OFF, once with memory ON.
    5. Learning is proven when B's memory-ON run recalls A and cites it.

``learning_proven`` is computed from the actual recall result. It is never
hard-coded to true, and the demo reports honestly if the loop did not close.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlmodel import Session

from app.schemas.agent import (
    ResolveRequest,
    SimulatedActionRequest,
)
from app.schemas.incident import IncidentCreate
from app.schemas.system import DemoRunResponse, DemoScenarioSummary
from app.services.agent_service import AgentService
from app.services.incident_service import IncidentService
from app.utils.logging import get_logger

log = get_logger("demo.scenario")

# --------------------------------------------------------------------------
# Incident A: the experience that gets retained.
# --------------------------------------------------------------------------
INCIDENT_A: Dict[str, Any] = {
    "key": "A",
    "label": "Incident A - the experience to be learned",
    "title": "checkout-api returning 5xx after v2.9.0 rollout",
    "service": "checkout-api",
    "severity": "high",
    "status": "active",
    "description": (
        "Beginning right after the v2.9.0 rollout, checkout-api began rejecting requests "
        "with 5xx responses. The database connection pool sits at 99% utilization and "
        "requests are queueing while they wait for a connection. Callers see failures and "
        "p99 latency has tripled."
    ),
    "signals": [
        "5xx rate 21% (baseline 0.9%)",
        "connection pool 99% utilized",
        "requests queueing for a database connection",
    ],
    "metrics": {"error_rate": 21.0, "pool_utilization": 99.0, "p99_latency_ms": 6400},
    "deployment_version": "v2.9.0",
    "recent_change": "deploy v2.9.0 (connection handling change)",
    "resolution": {
        "root_cause": (
            "v2.9.0 changed connection handling so database connections were never returned "
            "to the pool, exhausting it and starving the request path."
        ),
        "action_taken": "Rolled back checkout-api from v2.9.0 to v2.8.4",
        "failed_action": "Restarting the pods did not help; every new pod re-leaked connections.",
        "outcome": "5xx rate fell from 21% to 0.8% within 2 minutes of the rollback.",
        "lesson": (
            "If a checkout-api release is followed by rising 5xx and a saturated connection "
            "pool, suspect leaked connections and roll back before investigating further."
        ),
    },
}

# --------------------------------------------------------------------------
# Incident B: same operational reality, deliberately different wording.
# --------------------------------------------------------------------------
INCIDENT_B: Dict[str, Any] = {
    "key": "B",
    "label": "Incident B - the same problem, described differently",
    "title": "Checkout path degraded, requests stuck waiting on datastore",
    "service": "checkout-api",
    "severity": "critical",
    "status": "active",
    # Deliberately avoids incident A's phrasing. It never says "5xx", never says
    # "connection pool", never says "exhausted", and quotes no percentage the
    # same way. It describes the same operational reality through a customer
    # complaint and a different release: workers starved of a database
    # connection after a shipment.
    "description": (
        "Customers report the checkout path is hanging. Workers sit parked waiting "
        "for a free database connection, and the datastore side reports that every "
        "connection slot is already in use. Response times are far above the range "
        "we normally see. The team shipped release 2.10.1 about ten minutes before "
        "this started. Dashboards show a sharp climb in unsuccessful checkouts and a "
        "much deeper tail on end-to-end latency."
    ),
    "signals": [
        "unsuccessful checkout ratio 24%",
        "every connection slot in use",
        "tail latency 7.1s",
        "release 2.10.1 shipped 10 minutes before onset",
    ],
    "metrics": {"error_rate": 24.0, "pool_utilization": 99.0, "p99_latency_ms": 7100},
    "deployment_version": "v2.10.1",
    "recent_change": "release 2.10.1 shipped 10 minutes before onset",
}

EXPECTED_STEPS: List[str] = [
    "Incident A is investigated with memory ON and initially has no relevant history.",
    "Incident A is resolved and its structured experience is retained to memory.",
    "Incident B arrives for the same service and failure pattern, worded differently.",
    "Incident B is investigated with memory OFF, giving a generic, low-confidence plan.",
    "Incident B is investigated with memory ON and recalls incident A.",
    "The response cites A's root cause, the action that worked, and A's outcome.",
]


def _create_payload(data: Dict[str, Any]) -> IncidentCreate:
    return IncidentCreate(
        title=data["title"],
        service=data["service"],
        severity=data["severity"],
        status="active",
        description=data["description"],
        signals=list(data["signals"]),
        metrics=dict(data["metrics"]),
        deployment_version=data["deployment_version"],
        recent_change=data["recent_change"],
    )


def scenario_summary() -> DemoScenarioSummary:
    """Public description of the scenario, for ``GET /api/demo/scenarios``."""
    return DemoScenarioSummary(
        id="learning-loop-a-then-b",
        title="Incident A is learned, then applied to a differently-worded Incident B",
        narrative=(
            "A checkout-api release leaks database connections and exhausts the pool. "
            "The agent investigates, a human approves a rollback, the incident is "
            "resolved and the experience is retained to organisational memory. A later "
            "checkout-api release shows the same operational failure described in "
            "completely different words. The agent recalls the earlier incident, cites its "
            "root cause, its successful action and its outcome, and recommends the remedy "
            "that is already known to work."
        ),
        incident_a={
            "title": INCIDENT_A["title"],
            "service": INCIDENT_A["service"],
            "deployment_version": INCIDENT_A["deployment_version"],
            "signals": INCIDENT_A["signals"],
        },
        incident_b={
            "title": INCIDENT_B["title"],
            "service": INCIDENT_B["service"],
            "deployment_version": INCIDENT_B["deployment_version"],
            "signals": INCIDENT_B["signals"],
        },
        expected=EXPECTED_STEPS,
    )


def run(session: Session) -> DemoRunResponse:
    """Execute the whole learning loop and report what actually happened."""
    incidents = IncidentService(session)
    agent = AgentService(session)
    steps: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------- 1. A
    incident_a = incidents.create(_create_payload(INCIDENT_A))
    a_investigation = agent.investigate(incident_a.id, memory_enabled=True)
    steps.append(
        {
            "step": 1,
            "name": "Investigate Incident A (memory ON)",
            "incident_id": incident_a.id,
            "detail": (
                f"{a_investigation.memory_count} prior experience(s) recalled; "
                f"confidence {a_investigation.confidence}"
            ),
            "memory_count": a_investigation.memory_count,
            "memory_source": a_investigation.memory_source,
            "recommended_action": (
                a_investigation.recommended_action.action
                if a_investigation.recommended_action
                else None
            ),
            "confidence": a_investigation.confidence,
        }
    )

    # ------------------------------------------- 2. approve + simulate action
    recommended = a_investigation.recommended_action
    action_text = recommended.action if recommended else "Investigate checkout-api"
    action_result = agent.simulate_action(
        incident_a.id,
        SimulatedActionRequest(
            action=action_text,
            approved=True,
            approved_by="demo-operator",
            action_type=recommended.action_type if recommended else None,
        ),
    )
    steps.append(
        {
            "step": 2,
            "name": "Human approves and simulates the recommended action",
            "incident_id": incident_a.id,
            "action": action_result.action,
            "action_type": action_result.action_type,
            "success": action_result.success,
            "message": action_result.message,
            "telemetry": [t.model_dump() for t in action_result.telemetry],
            "simulated": action_result.simulated,
        }
    )

    # ------------------------------------------------------- 3. resolve + retain
    resolution = INCIDENT_A["resolution"]
    resolve_result = agent.resolve_incident(
        incident_a.id,
        ResolveRequest(
            root_cause=resolution["root_cause"],
            action_taken=resolution["action_taken"],
            failed_action=resolution["failed_action"],
            outcome=resolution["outcome"],
            lesson=resolution["lesson"],
            resolution_time_seconds=420.0,
            retain=True,
        ),
    )
    steps.append(
        {
            "step": 3,
            "name": "Resolve Incident A and retain the experience",
            "incident_id": incident_a.id,
            "status": resolve_result.status,
            "retained": resolve_result.retained,
            "retain_status": resolve_result.retain_status,
            "memory_event_id": resolve_result.memory_event_id,
        }
    )

    # ---------------------------------------------------------------- 4. B
    incident_b = incidents.create(_create_payload(INCIDENT_B))

    b_off = agent.investigate(incident_b.id, memory_enabled=False)
    steps.append(
        {
            "step": 4,
            "name": "Investigate Incident B with memory OFF (control)",
            "incident_id": incident_b.id,
            "mode": b_off.mode,
            "memory_count": b_off.memory_count,
            "recommended_action": (
                b_off.recommended_action.action if b_off.recommended_action else None
            ),
            "recommended_action_type": (
                b_off.recommended_action.action_type if b_off.recommended_action else None
            ),
            "confidence": b_off.confidence,
            "limitations": b_off.limitations,
        }
    )

    b_on = agent.investigate(incident_b.id, memory_enabled=True)
    steps.append(
        {
            "step": 5,
            "name": "Investigate Incident B with memory ON",
            "incident_id": incident_b.id,
            "mode": b_on.mode,
            "memory_count": b_on.memory_count,
            "memory_source": b_on.memory_source,
            "recommended_action": (
                b_on.recommended_action.action if b_on.recommended_action else None
            ),
            "recommended_action_type": (
                b_on.recommended_action.action_type if b_on.recommended_action else None
            ),
            "confidence": b_on.confidence,
        }
    )

    # ------------------------------------------------------- 5. the evidence
    evidence_dumps = [e.model_dump() for e in b_on.memory_evidence]
    recalled_a = [
        e for e in evidence_dumps if e.get("source_incident_id") == incident_a.id
    ]
    evidence = recalled_a[0] if recalled_a else None

    steps.append(
        {
            "step": 6,
            "name": "Historical evidence used for Incident B",
            "incident_id": incident_b.id,
            "retrieved": bool(evidence),
            "historical_incident_id": evidence.get("source_incident_id") if evidence else None,
            "historical_root_cause": evidence.get("historical_root_cause") if evidence else None,
            "historical_action": evidence.get("historical_action") if evidence else None,
            "historical_outcome": evidence.get("historical_outcome") if evidence else None,
            "historical_lesson": evidence.get("historical_lesson") if evidence else None,
            "why_relevant": evidence.get("why_relevant") if evidence else None,
            "relevance": evidence.get("relevance") if evidence else None,
            "relevance_method": evidence.get("relevance_method") if evidence else None,
        }
    )

    # ------------------------------------------------------ 6. verify claim
    learning_proven = bool(
        evidence
        and evidence.get("historical_root_cause")
        and evidence.get("historical_action")
        and evidence.get("historical_outcome")
        and evidence.get("why_relevant")
    )

    if learning_proven:
        summary = (
            f"Learning loop proven. Incident {incident_b.id} was described in different words "
            f"from incident {incident_a.id}, yet the agent recalled {incident_a.id} from memory "
            f"and used its root cause, its successful action and its outcome to recommend "
            f"'{b_on.recommended_action.action if b_on.recommended_action else 'no action'}' "
            f"at {b_on.confidence} confidence. The same incident with memory OFF produced "
            f"'{b_off.recommended_action.action if b_off.recommended_action else 'no action'}' "
            f"at {b_off.confidence} confidence."
        )
    else:
        summary = (
            f"Learning loop NOT proven. Investigating {incident_b.id} with memory ON recalled "
            f"{b_on.memory_count} experience(s) but none of them was {incident_a.id}. "
            "The demo is reporting this rather than claiming a result it did not achieve."
        )

    log.info(
        "demo scenario complete",
        extra={
            "event_incident_a": incident_a.id,
            "event_incident_b": incident_b.id,
            "event_learning_proven": learning_proven,
        },
    )

    scenario = scenario_summary().model_dump()
    scenario["incident_a"]["id"] = incident_a.id
    scenario["incident_b"]["id"] = incident_b.id

    return DemoRunResponse(
        scenario=scenario,
        steps=steps,
        learning_proven=learning_proven,
        summary=summary,
    )
