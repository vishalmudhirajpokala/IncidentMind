"""Demo routes.

Demo Mode must be reliable when external APIs are down. These endpoints make
that explicit: the scenario is deterministic, and Reset Demo restores the exact
seeded state so the demo can be re-run identically.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.demo.scenarios import run as run_scenario
from app.demo.scenarios import scenario_summary
from app.schemas.system import DemoRunResponse, DemoScenarioSummary
from app.utils.logging import get_logger
from seed.seed_incidents import reset_and_seed

log = get_logger("api.demo")

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get(
    "/status",
    summary="Demo mode status and which providers are actually live",
)
def demo_status() -> Dict[str, Any]:
    """Whether the deployment is in demo mode and which providers are wired up.

    Credentials are never echoed back, only whether they are present.
    """
    return {
        "demo_mode": settings.DEMO_MODE,
        "app_env": settings.APP_ENV,
        "memory_provider": settings.MEMORY_PROVIDER,
        "memory_configured": settings.hindsight_configured,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": settings.llm_configured,
        "llm_model": settings.LLM_MODEL,
        "notes": (
            "With no external credentials IncidentMind runs in demo mode: the local "
            "memory mirror and the deterministic analyst are used, and results are "
            "labelled as such."
        ),
    }


@router.get(
    "/scenarios",
    response_model=DemoScenarioSummary,
    summary="Describe the deterministic learning-loop scenario",
)
def scenarios() -> DemoScenarioSummary:
    return scenario_summary()


@router.post(
    "/run",
    response_model=DemoRunResponse,
    summary="Execute the full learning loop and report the evidence",
    description=(
        "Runs incident A to resolution and retention, then investigates a "
        "differently-worded incident B with memory OFF and memory ON. "
        "learning_proven is computed from the actual recall result, so if the "
        "loop does not close the response says so."
    ),
)
def run(session: Session = Depends(get_session)) -> DemoRunResponse:
    return run_scenario(session)


@router.post(
    "/reset",
    summary="Restore the seeded demo state",
    description=(
        "Deletes every incident, investigation run and memory event, then "
        "reseeds the reference corpus. Use before re-running the demo so the "
        "sequence is identical each time."
    ),
)
def reset(session: Session = Depends(get_session)) -> Dict[str, Any]:
    cleared = reset_and_seed(session)
    log.info("demo state reset", extra={"event_cleared": cleared})
    return {
        "reset": True,
        "cleared": cleared,
        "note": "Seeded state restored. Run POST /api/demo/run to replay the learning loop.",
    }


@router.get(
    "/history",
    summary="Investigation history across all incidents",
)
def history(
    limit: int = Query(50, ge=1, le=200), session: Session = Depends(get_session)
) -> Dict[str, Any]:
    from app.services.agent_service import AgentService

    return {"investigations": AgentService(session).history(limit=limit)}
