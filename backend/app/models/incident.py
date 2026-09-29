"""Incident persistence model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Timezone-aware now. All datetimes in this app are tz-aware."""
    return datetime.now(timezone.utc)


class Incident(SQLModel, table=True):
    """A production incident and everything observed about it."""

    __tablename__ = "incident"

    id: str = Field(primary_key=True)
    title: str
    service: str = Field(index=True)
    severity: str = "medium"
    status: str = Field(default="active", index=True)

    # --- what the operator observed -------------------------------------
    description: Optional[str] = None
    signals: list = Field(default_factory=list, sa_column=Column(JSON))
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # --- what changed ---------------------------------------------------
    deployment_version: Optional[str] = None
    recent_change: Optional[str] = None

    # --- outcome --------------------------------------------------------
    started_at: Optional[datetime] = Field(default=None, nullable=True)
    detected_at: Optional[datetime] = Field(default=None, nullable=True)
    resolved_at: Optional[datetime] = Field(default=None, nullable=True)
    resolution_time_seconds: Optional[float] = None

    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    failed_action: Optional[str] = None
    outcome: Optional[str] = None
    lesson: Optional[str] = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
