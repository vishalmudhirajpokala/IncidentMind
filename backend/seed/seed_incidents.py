"""Deterministic seed data for IncidentMind.

Two entry points:

  * ``seed_incidents(session)``   - idempotent upsert of the reference corpus
  * ``reset_and_seed(session)``   - wipe incidents, memories and investigations,
                                    then reseed. This is what "Reset Demo" calls.

The corpus is organised into failure families so that a fresh incident in any
family has genuine historical experience to recall.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlmodel import Session

from app.database import create_all, session_scope
from app.models.incident import Incident, utcnow
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.memory_repository import MemoryRepository

# Each entry is one resolved incident. Signals and metrics are recorded so the
# relevance scorer and the simulated-action telemetry have real inputs.
SEED_INCIDENTS: List[Dict[str, Any]] = [
    # ---------------- Family A: connection pool exhaustion ----------------
    {
        "id": "INC-001",
        "title": "DB connection pool exhaustion after v2.8.1 deployment",
        "service": "checkout-api",
        "severity": "high",
        "status": "resolved",
        "deployment_version": "v2.8.1",
        "recent_change": "deploy v2.8.1 (query client upgrade)",
        "description": (
            "Intermittent 503 errors rose from 1.2% to 18%. Database connection pool "
            "utilization reached 96% within 4 minutes. Failures started 3 minutes after "
            "the deployment and the pool never recovered."
        ),
        "signals": [
            "error_rate 18% (baseline 1.2%)",
            "connection pool 96% utilized",
            "request queue depth rising",
        ],
        "metrics": {"error_rate": 18.0, "pool_utilization": 96.0, "p99_latency_ms": 3200},
        "root_cause": (
            "v2.8.1 changed the database query client so connections were held for the "
            "duration of downstream calls, doubling concurrent connection demand and "
            "exhausting the pool."
        ),
        "action_taken": "Rolled back checkout-api from v2.8.1 to v2.8.0",
        "failed_action": "Restarting instances did not help; the leak reproduced on every new pod.",
        "outcome": "Error rate fell from 18% to 1.4% within 3 minutes of the rollback.",
        "resolution_time_seconds": 272,
        "lesson": (
            "If a checkout-api deploy is followed by 503s and pool utilization above 90%, "
            "suspect the query client holding connections and roll back first."
        ),
    },
    {
        "id": "INC-002",
        "title": "Connection pool saturation during Black Friday traffic",
        "service": "checkout-api",
        "severity": "critical",
        "status": "resolved",
        "deployment_version": "v2.8.2",
        "recent_change": "holiday traffic ramp",
        "description": (
            "Connection pool saturated during the holiday traffic spike. 503 errors peaked "
            "at 25% and connection waits exceeded 30 seconds."
        ),
        "signals": [
            "error_rate 25%",
            "connection waits > 30s",
            "pool exhaustion under load",
        ],
        "metrics": {"error_rate": 25.0, "pool_utilization": 99.0, "p99_latency_ms": 30000},
        "root_cause": (
            "Pool size of 50 was too small for holiday traffic, and an incomplete request "
            "cleanup path leaked connections."
        ),
        "action_taken": "Increased checkout-api pool size from 50 to 200 and fixed the connection leak",
        "failed_action": "A restart reset the symptom temporarily and the leak returned within the hour.",
        "outcome": "Error rate dropped to 3% under holiday load.",
        "resolution_time_seconds": 495,
        "lesson": (
            "Pool exhaustion under a traffic ramp needs both a larger pool and a leak fix; "
            "a restart alone is not a fix."
        ),
    },
    {
        "id": "INC-003",
        "title": "Stale connection pool causing 503s after query change",
        "service": "orders-api",
        "severity": "high",
        "status": "resolved",
        "deployment_version": "v2.9.0",
        "recent_change": "new orders database query",
        "description": (
            "503 errors began after deploying a new orders database query. The connection "
            "pool reached 98% utilization within 5 minutes and connections were never "
            "returned to the available state."
        ),
        "signals": ["error_rate 15%", "connection pool 98%", "connections not returned"],
        "metrics": {"error_rate": 15.0, "pool_utilization": 98.0, "p99_latency_ms": 2800},
        "root_cause": (
            "The new query did not close its connections, so the pool never returned them "
            "to the available state."
        ),
        "action_taken": "Fixed the orders-api query to use context managers and raised the pool size",
        "failed_action": "Scaling replicas only multiplied the number of leaking pools.",
        "outcome": "Error rate returned to baseline within 5 minutes.",
        "resolution_time_seconds": 402,
        "lesson": (
            "When a new query lands alongside 503s and a saturated pool, check connection "
            "lifecycle before scaling out."
        ),
    },
    # ---------------- Family B: deployment regression --------------------
    {
        "id": "INC-004",
        "title": "API latency spike after v2.8.3 deployment",
        "service": "payment-gateway",
        "severity": "high",
        "status": "resolved",
        "deployment_version": "v2.8.3",
        "recent_change": "deploy v2.8.3 (sorting rewrite)",
        "description": (
            "Latency rose from 200ms to 1.2s and the error rate from 0.5% to 12% with no "
            "change in request volume."
        ),
        "signals": ["p99 latency 1200ms", "error_rate 12%", "cpu saturation on serving tier"],
        "metrics": {"error_rate": 12.0, "p99_latency_ms": 1200, "cpu_utilization": 94.0},
        "root_cause": "An inefficient sorting algorithm in v2.8.3 saturated CPU on the serving tier.",
        "action_taken": "Rolled back payment-gateway from v2.8.3 to v2.8.2",
        "failed_action": "Adding replicas did not reduce per-request CPU cost.",
        "outcome": "Latency returned to 200ms and the error rate to 0.4%.",
        "resolution_time_seconds": 318,
        "lesson": (
            "Flat request volume with a latency and error spike after a deploy is a "
            "regression, not a capacity problem: roll back first."
        ),
    },
    {
        "id": "INC-005",
        "title": "Timeout errors after caching layer change",
        "service": "user-profile",
        "severity": "medium",
        "status": "resolved",
        "deployment_version": "v2.8.4",
        "recent_change": "caching layer upgrade",
        "description": (
            "Request timeouts rose from 2% to 15% and users could not load profiles. "
            "Traffic volume was unchanged."
        ),
        "signals": ["timeout rate 15%", "stale cache reads", "thundering herd on backend"],
        "metrics": {"error_rate": 15.0, "timeout_rate": 15.0, "p99_latency_ms": 5000},
        "root_cause": (
            "Cache invalidation produced stale reads and a thundering herd against the "
            "backend."
        ),
        "action_taken": "Fixed the user-profile cache TTL and added a cache warming routine",
        "failed_action": "Restarting the cache nodes cleared the herd but it returned.",
        "outcome": "Timeout rate dropped to 1%.",
        "resolution_time_seconds": 192,
        "lesson": (
            "Timeout spikes with unchanged traffic usually mean a cache stampede; warm the "
            "cache rather than restarting nodes."
        ),
    },
    # ---------------- Family C: dependency timeout cascade ---------------
    {
        "id": "INC-006",
        "title": "Authentication service timeout cascade",
        "service": "auth-service",
        "severity": "critical",
        "status": "resolved",
        "deployment_version": "v2.8.1",
        "recent_change": "database client upgrade",
        "description": (
            "Timeouts in auth-service cascaded to every dependent service, producing 503s "
            "across checkout and user-profile."
        ),
        "signals": ["timeout cascade", "503s across dependents", "connection pool exhausted"],
        "metrics": {"error_rate": 31.0, "timeout_rate": 28.0, "pool_utilization": 97.0},
        "root_cause": (
            "The auth database connection pool was exhausted under request load and the new "
            "connection rate was limited, so the failure propagated to all dependents."
        ),
        "action_taken": "Increased the auth DB pool size and optimized query performance",
        "failed_action": "Rolling back dependents did nothing because they were healthy.",
        "outcome": "All dependent services recovered and the timeout rate fell to 0.5%.",
        "resolution_time_seconds": 561,
        "lesson": (
            "A timeout cascade across several services usually originates in one saturated "
            "dependency; find that service before touching the callers."
        ),
    },
    # ---------------- Family D: memory pressure -------------------------
    {
        "id": "INC-007",
        "title": "Memory leak in notification service",
        "service": "notification-service",
        "severity": "medium",
        "status": "resolved",
        "deployment_version": "v2.9.1",
        "recent_change": "template rendering rewrite",
        "description": (
            "Memory grew steadily over 6 hours until the pods were OOM killed, producing "
            "503s after roughly 4 hours of uptime."
        ),
        "signals": ["memory growth over 6h", "OOM kills", "503s after 4h uptime"],
        "metrics": {"error_rate": 9.0, "memory_rss_mb": 3900, "uptime_hours": 4},
        "root_cause": "The notification handler never released email template resources.",
        "action_taken": "Fixed the template rendering leak and added memory pressure alerts",
        "failed_action": "Restarting the service only reset the growth curve.",
        "outcome": "No OOM incidents since the fix.",
        "resolution_time_seconds": 135,
        "lesson": (
            "Memory that climbs linearly and ends in OOM kills is a leak, not load: "
            "restarting buys hours, not a fix."
        ),
    },
    # ---------------- Family E: disk saturation -------------------------
    {
        "id": "INC-008",
        "title": "Disk saturation causing request failures",
        "service": "api-gateway",
        "severity": "high",
        "status": "resolved",
        "deployment_version": "v2.8.0",
        "recent_change": "debug logging enabled",
        "description": (
            "Disk usage reached 98% and request failures rose to 8% because log rotation "
            "had not run in 7 days."
        ),
        "signals": ["disk 98% full", "request failures 8%", "log rotation disabled"],
        "metrics": {"error_rate": 8.0, "disk_utilization": 98.0, "p99_latency_ms": 900},
        "root_cause": "Log rotation was disabled while debug logging wrote excessive data.",
        "action_taken": "Re-enabled log rotation on api-gateway and rotated old logs immediately",
        "failed_action": "Adding gateway replicas made the disk fill faster.",
        "outcome": "Disk usage dropped to 45% and the error rate returned to baseline.",
        "resolution_time_seconds": 210,
        "lesson": (
            "Disk saturation plus 503s on the gateway is usually logging volume; check "
            "rotation before adding capacity."
        ),
    },
]


def _to_model(data: Dict[str, Any]) -> Incident:
    now = utcnow()
    return Incident(
        id=data["id"],
        title=data["title"],
        service=data["service"],
        severity=data["severity"],
        status=data["status"],
        description=data.get("description"),
        signals=list(data.get("signals") or []),
        metrics=dict(data.get("metrics") or {}),
        deployment_version=data.get("deployment_version"),
        recent_change=data.get("recent_change"),
        started_at=now,
        detected_at=now,
        resolved_at=now,
        resolution_time_seconds=data.get("resolution_time_seconds"),
        root_cause=data.get("root_cause"),
        action_taken=data.get("action_taken"),
        failed_action=data.get("failed_action"),
        outcome=data.get("outcome"),
        lesson=data.get("lesson"),
        created_at=now,
        updated_at=now,
    )


def seed_incidents(session: Session) -> int:
    """Insert the reference corpus. Idempotent: existing ids are updated."""
    repo = IncidentRepository(session)
    created = 0
    for data in SEED_INCIDENTS:
        existing = repo.get(data["id"])
        if existing is not None:
            continue
        repo.create(_to_model(data))
        created += 1
    return created


def reset_and_seed(session: Session) -> Dict[str, int]:
    """Wipe all runtime state and restore the seed. Used by Reset Demo."""
    investigations = InvestigationRepository(session)
    memories = MemoryRepository(session)
    incidents = IncidentRepository(session)

    cleared = {
        "investigations": investigations.delete_all(),
        "memories": memories.delete_all(),
        "incidents": incidents.delete_all(),
    }
    created = seed_incidents(session)
    cleared["seeded"] = created
    return cleared


def main() -> None:
    create_all()
    with session_scope() as session:
        count = seed_incidents(session)
        print(f"Seed complete: {count} incident(s) inserted, {len(SEED_INCIDENTS)} total defined.")


if __name__ == "__main__":
    main()
