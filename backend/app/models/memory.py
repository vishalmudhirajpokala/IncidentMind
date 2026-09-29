"""Memory event persistence model.

Each row is a *local mirror* of an experience that was retained to persistent
memory. The mirror exists so that:
  * the demo and the UI can show what organisational memory contains even when
    the external memory service is unreachable
  * we can prove whether a retain reached the external service or not

``content`` is the exact text sent to the memory provider. ``event_metadata``
holds the structured incident fields used for deterministic local retrieval.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.incident import utcnow


class MemoryEvent(SQLModel, table=True):
    """One retained organisational experience."""

    __tablename__ = "memoryevent"

    id: str = Field(primary_key=True)
    incident_id: Optional[str] = Field(default=None, index=True)

    # experience | lesson | observation
    event_type: str = Field(default="experience", index=True)

    # title / symptoms text shown as a memory card in the UI
    title: Optional[str] = None
    symptoms: Optional[str] = None

    # exact narrative retained to the memory provider
    content: Optional[str] = Column(Text, nullable=True)

    # structured fields, used for deterministic local matching
    event_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # which provider actually accepted the write
    provider: Optional[str] = Field(default=None, index=True)
    external_retained: bool = Field(default=False)
    external_ids: list = Field(default_factory=list, sa_column=Column(JSON))
    external_error: Optional[str] = None

    retained_at: datetime = Field(default_factory=utcnow, index=True)
