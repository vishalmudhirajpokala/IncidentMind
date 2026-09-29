"""Memory and provider Pydantic schemas.

`MemoryEvidence` is the schema that makes the learning loop provable from the
outside: for every recalled historical experience it exposes the historical
incident id, its root cause, the action that worked, the outcome, and why it
was judged relevant. It deliberately contains no chain-of-thought.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderStatus(BaseModel):
    """Health of an external dependency. Safe to expose; never has credentials."""

    name: str
    mode: Literal["live", "demo", "unavailable"] = "unavailable"
    available: bool = False
    detail: Optional[str] = None
    latency_ms: Optional[int] = None


class MemoryEvidence(BaseModel):
    """One recalled historical experience, with provenance and relevance."""

    memory_id: str
    source_incident_id: Optional[str] = None

    historical_title: Optional[str] = None
    historical_service: Optional[str] = None
    historical_symptoms: Optional[str] = None
    historical_root_cause: Optional[str] = None
    historical_action: Optional[str] = None
    historical_outcome: Optional[str] = None
    historical_lesson: Optional[str] = None

    why_relevant: str = ""
    matched_on: List[str] = Field(default_factory=list)

    rank: int = 0
    # Hindsight's recall API does not return a similarity score. When this is
    # populated it is always computed locally, and the method used is reported
    # in `relevance_method`. A score is never attributed to Hindsight.
    relevance: Optional[float] = None
    relevance_method: Optional[str] = None

    provider: str = "unknown"
    text: Optional[str] = None


class MemoryRecallResponse(BaseModel):
    query: str
    memories: List[MemoryEvidence] = Field(default_factory=list)
    count: int = 0
    source: str = "none"
    status: str = "ok"
    detail: Optional[str] = None


class MemoryEventRead(BaseModel):
    """A retained memory record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: Optional[str] = None
    event_type: str
    title: Optional[str] = None
    symptoms: Optional[str] = None
    content: Optional[str] = None
    provider: Optional[str] = None
    external_retained: bool = False
    external_ids: List[str] = Field(default_factory=list)
    retained_at: Optional[datetime] = None
    event_metadata: Dict[str, Any] = Field(default_factory=dict)


class RetainRequest(BaseModel):
    """Structured experience captured when an incident is resolved."""

    incident_id: str
    service: Optional[str] = None
    symptoms: Optional[str] = None
    signals: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    deployment: Optional[str] = None
    investigation: List[str] = Field(default_factory=list)
    root_cause: str
    actions_tried: List[str] = Field(default_factory=list)
    successful_action: Optional[str] = None
    failed_action: Optional[str] = None
    outcome: str
    resolution_time: Optional[str] = None
    lesson: str


class RetainResponse(BaseModel):
    incident_id: str
    success: bool
    memory_event_id: Optional[str] = None
    provider: str
    external_retained: bool
    status: Literal["retained", "retained_locally", "failed"] = "retained"
    detail: Optional[str] = None
    external_ids: List[str] = Field(default_factory=list)
