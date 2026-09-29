"""System-level schemas: health, metrics, demo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.memory import ProviderStatus


class HealthResponse(BaseModel):
    """Health never fails when an optional dependency is down."""

    status: str
    app: str
    version: str
    env: str
    demo_mode: bool
    database: ProviderStatus
    memory: ProviderStatus
    llm: ProviderStatus


class MetricsOverview(BaseModel):
    """Counts derived from the database. No fabricated percentages."""

    incidents_total: int
    incidents_active: int
    incidents_resolved: int
    by_severity: Dict[str, int]
    by_service: Dict[str, int]
    investigations_total: int
    investigations_memory_on: int
    investigations_memory_off: int
    memory_events_total: int
    memory_events_external: int
    memory_events_local_only: int
    average_confidence_memory_on: Optional[float] = None
    average_confidence_memory_off: Optional[float] = None

    # Mean of the durations that were actually recorded. Null when no incident
    # has one. `incidents_with_measured_resolution` is exposed alongside it so a
    # reader can see the size of the sample instead of trusting a mean of one.
    average_resolution_time_seconds: Optional[float] = None
    incidents_with_measured_resolution: int = 0

    providers: Dict[str, ProviderStatus]


class DemoScenarioSummary(BaseModel):
    id: str
    title: str
    narrative: str
    incident_a: Dict[str, Any]
    incident_b: Dict[str, Any]
    expected: List[str]


class DemoRunResponse(BaseModel):
    """Result of executing the deterministic learning-loop demo."""

    scenario: Dict[str, Any]
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    learning_proven: bool = False
    summary: str = ""
