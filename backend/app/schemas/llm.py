"""The structured contract every LLM provider must satisfy.

Both the live Groq provider and the deterministic provider validate into
`LLMInvestigation`, so the agent service has one shape to work with.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.agent import Hypothesis, RecommendedAction


class LLMInvestigation(BaseModel):
    """Structured analysis returned by any LLM provider."""

    summary: str = Field(..., min_length=1, max_length=1200)
    reasoning_summary: str = Field(default="", max_length=1200)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    recommended_action: Optional[RecommendedAction] = None
    limitations: Optional[str] = None
    memory_used: List[str] = Field(default_factory=list)
