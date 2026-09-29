"""Investigation run repository."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.investigation import InvestigationRun


class InvestigationRepository:
    """Data access for recorded investigations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **fields: Any) -> InvestigationRun:
        run = InvestigationRun(id=f"inv-{uuid.uuid4().hex[:12]}", **fields)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def all(self, limit: int = 200) -> List[ InvestigationRun]:
        statement = (
            select(InvestigationRun)
            .order_by(InvestigationRun.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def for_incident(self, incident_id: str) -> List[InvestigationRun]:
        statement = (
            select(InvestigationRun)
            .where(InvestigationRun.incident_id == incident_id)
            .order_by(InvestigationRun.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def by_mode(self, mode: str) -> List[InvestigationRun]:
        statement = select(InvestigationRun).where(InvestigationRun.mode == mode)
        return list(self.session.exec(statement).all())

    def average_confidence(self, mode: str) -> Optional[float]:
        rows = self.by_mode(mode)
        if not rows:
            return None
        return round(sum(r.confidence for r in rows) / len(rows), 4)

    def delete_all(self) -> int:
        rows = self.all(limit=10_000)
        for row in rows:
            self.session.delete(row)
        self.session.commit()
        return len(rows)
