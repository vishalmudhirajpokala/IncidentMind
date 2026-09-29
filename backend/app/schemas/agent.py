"""Agent Pydantic schemas: investigation, recommendation, simulated actions."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.memory import MemoryEvidence, ProviderStatus


class Hypothesis(BaseModel):
    cause: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    action: str = Field(..., min_length=3)
    reason: str
    risk: str = Field(default="medium", pattern="^(low|medium|high)$")
    action_type: str = "investigate"
    # The action layer is always simulated and always human-approved.
    simulated: bool = True
    requires_approval: bool = True


class InvestigationRequest(BaseModel):
    memory_enabled: bool = Field(
        default=True,
        description="False runs the memory-OFF path: current incident + LLM only.",
    )
    extra_context: Optional[str] = None


class InvestigationResult(BaseModel):
    incident: Dict[str, Any]
    mode: Literal["memory_on", "memory_off"]

    summary: str
    reasoning_summary: str
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    investigation_steps: List[str] = Field(default_factory=list)

    recommended_action: Optional[RecommendedAction] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # --- memory evidence -------------------------------------------------
    memory_enabled: bool = True
    memory_count: int = 0
    memory_evidence: List[MemoryEvidence] = Field(default_factory=list)
    memory_source: str = "none"
    memory_status: str = "disabled"
    memory_query: Optional[str] = None
    memory_detail: Optional[str] = None

    # --- providers -------------------------------------------------------
    memory_provider: Optional[ProviderStatus] = None
    llm_provider: Optional[ProviderStatus] = None

    limitations: Optional[str] = None
    requires_human_approval: bool = True
    request_id: str = ""
    duration_ms: int = 0


class SimulatedActionRequest(BaseModel):
    action: str = Field(..., min_length=2, max_length=400)
    approved: bool = Field(
        default=False,
        strict=True,
        description=(
            "Must be the JSON literal true. IncidentMind never acts without explicit "
            "human approval; the API rejects unapproved actions with 409. Strictly "
            "typed so a loose string is a validation error rather than a silent yes."
        ),
    )
    approved_by: Optional[str] = Field(
        default=None, description="Recorded human approver. No auth in the MVP."
    )
    action_type: Optional[str] = None


class TelemetryPoint(BaseModel):
    metric: str
    before: float
    after: float
    unit: str = "percent"


class SimulatedActionResult(BaseModel):
    incident_id: str
    action: str
    action_type: str
    simulated: bool = True
    approved_by: Optional[str] = None
    success: bool
    message: str
    duration_seconds: float
    telemetry: List[TelemetryPoint] = Field(default_factory=list)
    notes: str = "Simulated only. No production system was contacted."


class ResolveRequest(BaseModel):
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    failed_action: Optional[str] = None
    outcome: str = Field(default="resolved", min_length=1)
    lesson: Optional[str] = None
    resolution_time_seconds: Optional[float] = Field(default=None, ge=0)
    retain: bool = Field(
        default=True, description="Retain the resolved experience to memory immediately."
    )


class ResolveResponse(BaseModel):
    incident_id: str
    status: str
    outcome: str
    resolution_time_seconds: Optional[float] = None
    retained: bool = False
    retain_status: Optional[str] = None
    memory_event_id: Optional[str] = None
