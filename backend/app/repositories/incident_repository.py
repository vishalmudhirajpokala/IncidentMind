"""Incident repository."""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Session, select

from app.models.incident import Incident


class IncidentRepository:
    """Data access for incidents."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        self.session.commit()
        self.session.refresh(incident)
        return incident

    def get(self, incident_id: str) -> Optional[Incident]:
        return self.session.get(Incident, incident_id)

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        service: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Incident]:
        statement = select(Incident)
        if status:
            statement = statement.where(Incident.status == status)
        if service:
            statement = statement.where(Incident.service == service)
        if severity:
            statement = statement.where(Incident.severity == severity)
        statement = statement.order_by(Incident.created_at.desc()).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        return len(list(self.session.exec(select(Incident)).all()))

    def all(self) -> List[Incident]:
        return list(self.session.exec(select(Incident)).all())

    def next_id(self) -> str:
        """Allocate the next ``INC-NNN`` identifier."""
        existing = self.all()
        highest = 0
        for incident in existing:
            if incident.id.startswith("INC-"):
                try:
                    highest = max(highest, int(incident.id.split("-")[1]))
                except (IndexError, ValueError):
                    continue
        return f"INC-{highest + 1:03d}"

    def update(self, incident: Incident) -> Incident:
        self.session.add(incident)
        self.session.commit()
        self.session.refresh(incident)
        return incident

    def delete(self, incident_id: str) -> bool:
        incident = self.get(incident_id)
        if not incident:
            return False
        self.session.delete(incident)
        self.session.commit()
        return True

    def delete_all(self) -> int:
        incidents = self.all()
        for incident in incidents:
            self.session.delete(incident)
        self.session.commit()
        return len(incidents)
