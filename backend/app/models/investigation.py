"""Investigation run persistence model.

Every investigation (memory ON or memory OFF) is recorded so the learning loop
is auditable after the fact and so the metrics endpoint can report real numbers
instead of invented ones.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.incident import utcnow


class InvestigationRun(SQLModel, table=True):
    """A single agent investigation of an incident."""

    __tablename__ = "investigationrun"

    id: str = Field(primary_key=True)
    incident_id: str = Field(index=True)

    # memory_on | memory_off
    mode: str = Field(default="memory_on", index=True)

    summary: Optional[str] = None
    reasoning_summary: Optional[str] = None
    confidence: float = 0.0

    recommended_action: Optional[str] = None
    action_type: Optional[str] = None
    action_risk: Optional[str] = None

    hypotheses: list = Field(default_factory=list, sa_column=Column(JSON))
    memory_evidence: list = Field(default_factory=list, sa_column=Column(JSON))
    memory_count: int = 0
    memory_source: Optional[str] = None
    memory_status: Optional[str] = None

    llm_provider: Optional[str] = None
    llm_status: Optional[str] = None

    limitations: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None

    created_at: datetime = Field(default_factory=utcnow, index=True)
