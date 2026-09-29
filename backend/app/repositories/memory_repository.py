"""Memory event repository."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.memory import MemoryEvent


class MemoryRepository:
    """Data access for retained memory events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ---------------------------------------------------------------- write
    def create(
        self,
        *,
        incident_id: Optional[str] = None,
        event_type: str = "experience",
        title: Optional[str] = None,
        symptoms: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        external_retained: bool = False,
        external_ids: Optional[List[str]] = None,
        external_error: Optional[str] = None,
    ) -> MemoryEvent:
        event = MemoryEvent(
            id=f"mem-{uuid.uuid4().hex[:12]}",
            incident_id=incident_id,
            event_type=event_type,
            title=title,
            symptoms=symptoms,
            content=content,
            event_metadata=metadata or {},
            provider=provider,
            external_retained=external_retained,
            external_ids=external_ids or [],
            external_error=external_error,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    # ----------------------------------------------------------------- read
    def most_recent(self, limit: int = 20) -> List[MemoryEvent]:
        statement = (
            select(MemoryEvent)
            .order_by(MemoryEvent.retained_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def all_experiences(self) -> List[MemoryEvent]:
        statement = select(MemoryEvent).order_by(MemoryEvent.retained_at.desc())
        return list(self.session.exec(statement).all())

    def for_incident(self, incident_id: str) -> List[MemoryEvent]:
        statement = (
            select(MemoryEvent)
            .where(MemoryEvent.incident_id == incident_id)
            .order_by(MemoryEvent.retained_at.desc())
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        return len(self.all_experiences())

    def delete_all(self) -> int:
        events = self.all_experiences()
        for event in events:
            self.session.delete(event)
        self.session.commit()
        return len(events)
