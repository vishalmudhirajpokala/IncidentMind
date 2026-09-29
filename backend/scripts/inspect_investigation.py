"""Print one full investigation response so the output can be reviewed.

    python scripts/inspect_investigation.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_all, session_scope  # noqa: E402
from app.services.agent_service import AgentService  # noqa: E402
from app.services.incident_service import IncidentService  # noqa: E402
from app.demo.scenarios import INCIDENT_A, INCIDENT_B, _create_payload  # noqa: E402
from seed.seed_incidents import reset_and_seed  # noqa: E402

create_all()
with session_scope() as session:
    reset_and_seed(session)

with session_scope() as session:
    incidents = IncidentService(session)
    agent = AgentService(session)

    a = incidents.create(_create_payload(INCIDENT_A))
    agent.investigate(a.id, memory_enabled=True)
    agent.resolve_incident(
        a.id,
        __import__("app.schemas.agent", fromlist=["ResolveRequest"]).ResolveRequest(
            **INCIDENT_A["resolution"], resolution_time_seconds=420.0, retain=True
        ),
    )

    b = incidents.create(_create_payload(INCIDENT_B))
    result = agent.investigate(b.id, memory_enabled=True)

    print(json.dumps(result.model_dump(), indent=2, default=str))
