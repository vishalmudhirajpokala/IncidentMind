"""Incident service: CRUD and listing with filters."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.incident import Incident, utcnow
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate


class IncidentService:
    """Service layer for incident operations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = IncidentRepository(session)

    def create(self, payload: IncidentCreate) -> Incident:
        """Create an incident.

        The id is allocated from the same ``INC-NNN`` sequence the seed data
        uses, so ids are stable and human-referable across a reset.
        """
        incident = Incident(
            id=self.repo.next_id(),
            title=payload.title.strip(),
            service=payload.service.strip(),
            severity=payload.severity,
            status=payload.status,
            description=payload.description,
            signals=list(payload.signals or []),
            metrics=dict(payload.metrics or {}),
            deployment_version=payload.deployment_version,
            recent_change=payload.recent_change,
            started_at=payload.started_at or utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        return self.repo.create(incident)

    def get(self, incident_id: str) -> Incident:
        """Fetch one incident or raise 404."""
        incident = self.repo.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found",
            )
        return incident

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        service: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Incident]:
        return self.repo.list(
            skip=skip,
            limit=limit,
            status=status_filter,
            service=service,
            severity=severity,
        )

    def count(self) -> int:
        return self.repo.count()

    def update(self, incident_id: str, payload: IncidentUpdate) -> Incident:
        incident = self.get(incident_id)
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            if value is not None:
                setattr(incident, key, value)
        incident.updated_at = utcnow()
        return self.repo.update(incident)

    def delete(self, incident_id: str) -> None:
        self.get(incident_id)  # 404 if missing
        self.repo.delete(incident_id)

    def read_model(self, incident: Incident) -> IncidentRead:
        return IncidentRead.model_validate(incident)


def incident_to_dict(incident: Incident) -> Dict[str, Any]:
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
        "started_at": incident.started_at,
        "resolved_at": incident.resolved_at,
        "resolution_time_seconds": incident.resolution_time_seconds,
        "root_cause": incident.root_cause,
        "action_taken": incident.action_taken,
        "failed_action": incident.failed_action,
        "outcome": incident.outcome,
        "lesson": incident.lesson,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }
