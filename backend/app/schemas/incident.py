"""Incident Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    service: str = Field(..., min_length=1, max_length=120)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    status: str = Field(default="active", pattern="^(active|investigating|mitigated|resolved)$")
    description: Optional[str] = None
    signals: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    deployment_version: Optional[str] = None
    recent_change: Optional[str] = None
    started_at: Optional[datetime] = None


class IncidentCreate(IncidentBase):
    """Request body for creating an incident."""


class IncidentUpdate(BaseModel):
    """Partial update. Only provided fields are written."""

    title: Optional[str] = None
    severity: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(
        default=None, pattern="^(active|investigating|mitigated|resolved)$"
    )
    description: Optional[str] = None
    signals: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    failed_action: Optional[str] = None
    outcome: Optional[str] = None
    lesson: Optional[str] = None
    resolution_time_seconds: Optional[float] = None


class IncidentRead(IncidentBase):
    """Response schema for an incident."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_time_seconds: Optional[float] = None
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    failed_action: Optional[str] = None
    outcome: Optional[str] = None
    lesson: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
