"""Agent routes: investigate, approve and simulate, resolve, retain."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.agent import (
    InvestigationResult,
    ResolveRequest,
    ResolveResponse,
    SimulatedActionRequest,
    SimulatedActionResult,
)
from app.schemas.memory import RetainResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/incidents", tags=["agent"])


@router.post(
    "/{incident_id}/investigate",
    response_model=InvestigationResult,
    summary="Investigate an incident",
    description=(
        "Runs the full investigation loop: recall historical experience from "
        "organisational memory, analyse the assembled evidence, and recommend a "
        "reversible action. Nothing is executed. Set memory_enabled=false for the "
        "honest memory-OFF control path."
    ),
    responses={
        404: {"description": "Incident not found"},
        422: {"description": "Request body failed validation"},
    },
)
def investigate(
    incident_id: str,
    payload: Optional[Dict[str, Any]] = Body(default=None),
    memory_enabled: Optional[bool] = Query(
        None, description="Override for the memory ON/OFF path."
    ),
    session: Session = Depends(get_session),
) -> InvestigationResult:
    service = AgentService(session)
    body = payload or {}
    enabled = body.get("memory_enabled", memory_enabled)
    if enabled is None:
        enabled = True
    if not isinstance(enabled, bool):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'memory_enabled' must be a boolean.",
        )
    return service.investigate(
        incident_id,
        memory_enabled=enabled,
        extra_context=body.get("extra_context"),
    )


@router.post(
    "/{incident_id}/simulate-action",
    response_model=SimulatedActionResult,
    summary="Simulate a human-approved action",
    description=(
        "Executes a SIMULATED action with deterministic telemetry. Real "
        "infrastructure is never contacted. The request must include "
        "\"approved\": true; unapproved actions are rejected with 409."
    ),
    responses={
        404: {"description": "Incident not found"},
        409: {"description": "Action was not approved by a human"},
    },
)
def simulate_action(
    incident_id: str,
    payload: SimulatedActionRequest,
    session: Session = Depends(get_session),
) -> SimulatedActionResult:
    service = AgentService(session)
    return service.simulate_action(incident_id, payload)


@router.post(
    "/{incident_id}/resolve",
    response_model=ResolveResponse,
    summary="Resolve an incident",
    description=(
        "Marks the incident resolved and, by default, retains the structured "
        "experience to organisational memory in the same call."
    ),
    responses={404: {"description": "Incident not found"}},
)
def resolve(
    incident_id: str,
    payload: ResolveRequest,
    session: Session = Depends(get_session),
) -> ResolveResponse:
    service = AgentService(session)
    return service.resolve_incident(incident_id, payload)


@router.post(
    "/{incident_id}/retain",
    response_model=RetainResponse,
    summary="Retain a resolved incident to memory",
    description=(
        "Writes the structured experience of a resolved incident to persistent "
        "memory. Requires a recorded root cause; returns 409 otherwise. The "
        "response states whether the write reached the external memory service "
        "or only the local mirror."
    ),
    responses={
        404: {"description": "Incident not found"},
        409: {"description": "Incident has no recorded root cause"},
    },
)
def retain(
    incident_id: str, session: Session = Depends(get_session)
) -> RetainResponse:
    service = AgentService(session)
    return service.retain_incident(incident_id)
