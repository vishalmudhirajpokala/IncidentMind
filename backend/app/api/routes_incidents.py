"""Incident routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.services.agent_service import AgentService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentRead], summary="List incidents")
def list_incidents(
    skip: int = Query(0, ge=0, description="Rows to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum rows to return"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by incident status"
    ),
    service: Optional[str] = Query(None, description="Filter by service"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    session: Session = Depends(get_session),
) -> List[IncidentRead]:
    service_obj = IncidentService(session)
    incidents = service_obj.list(
        skip=skip, limit=limit, status_filter=status_filter, service=service, severity=severity
    )
    return [service_obj.read_model(i) for i in incidents]


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
def create_incident(
    payload: IncidentCreate, session: Session = Depends(get_session)
) -> IncidentRead:
    service = IncidentService(session)
    return service.read_model(service.create(payload))


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Get one incident",
    responses={404: {"description": "Incident not found"}},
)
def get_incident(
    incident_id: str, session: Session = Depends(get_session)
) -> IncidentRead:
    service = IncidentService(session)
    return service.read_model(service.get(incident_id))


@router.patch(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Update an incident",
    responses={404: {"description": "Incident not found"}},
)
def update_incident(
    incident_id: str, payload: IncidentUpdate, session: Session = Depends(get_session)
) -> IncidentRead:
    service = IncidentService(session)
    return service.read_model(service.update(incident_id, payload))


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    responses={404: {"description": "Incident not found"}},
)
def delete_incident(incident_id: str, session: Session = Depends(get_session)) -> None:
    IncidentService(session).delete(incident_id)


@router.get(
    "/{incident_id}/history",
    summary="Investigation history for an incident",
    responses={404: {"description": "Incident not found"}},
)
def incident_history(
    incident_id: str, limit: int = Query(50, ge=1, le=200), session: Session = Depends(get_session)
) -> dict:
    incident_service = IncidentService(session)
    incident_service.get(incident_id)  # 404 if missing
    agent = AgentService(session)
    return {
        "incident_id": incident_id,
        "investigations": agent.history(incident_id=incident_id, limit=limit),
    }
