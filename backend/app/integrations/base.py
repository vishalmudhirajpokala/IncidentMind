"""Provider interfaces.

Application and service code depends only on these interfaces. No provider
specific behaviour (HTTP paths, SDK calls, model names) is allowed to leak past
this module, which is what makes the real/LIVE path swappable for a mock
without touching business logic.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.schemas.memory import ProviderStatus


# ---------------------------------------------------------------------------
# memory
# ---------------------------------------------------------------------------
@dataclass
class RetrievedMemory:
    """A raw memory record returned by a memory provider.

    ``score`` is only populated when the provider actually returns one. Hindsight
    does not, so for that provider ``score`` stays None and the caller must
    compute its own relevance (and label it as locally computed).
    """

    id: str
    text: str = ""
    context: Optional[str] = None
    fact_type: Optional[str] = None
    occurred_start: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    score: Optional[float] = None
    provider: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetainOutcome:
    """Result of writing an experience to a memory provider."""

    success: bool
    provider: str
    external: bool
    external_ids: List[str] = field(default_factory=list)
    detail: Optional[str] = None


class MemoryProvider(abc.ABC):
    """Read/write access to organisational memory."""

    name: str = "memory"

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """True when this provider can actually be used."""

    @abc.abstractmethod
    def recall(self, query: str, *, limit: int = 5) -> List[RetrievedMemory]:
        """Return memories relevant to ``query``. Must not raise on transport
        failure; return an empty list and let ``health``/logging surface it."""

    @abc.abstractmethod
    def retain(
        self,
        content: str,
        *,
        context: str = "",
        document_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ) -> RetainOutcome:
        """Persist an experience. Must not raise on transport failure."""

    def retain_batch(
        self,
        items: List[Dict[str, Any]],
        *,
        document_id: Optional[str] = None,
    ) -> RetainOutcome:
        """Persist several labelled parts of one experience.

        Hindsight extracts *facts* from whatever it is given, so a single blob
        comes back split apart on recall. Retaining each field as its own item
        that shares a ``context`` marker keeps the experience reconstructable.
        Providers that do not need this may inherit this default.
        """
        outcomes = [
            self.retain(
                str(item.get("content", "")),
                context=str(item.get("context", "")),
                document_id=document_id,
                tags=item.get("tags"),
                timestamp=item.get("timestamp"),
            )
            for item in items
            if item.get("content")
        ]
        successes = [o for o in outcomes if o.success]
        return RetainOutcome(
            success=bool(successes),
            provider=self.name,
            external=successes[0].external if successes else False,
            external_ids=[i for o in successes for i in o.external_ids],
            detail=f"{len(successes)}/{len(outcomes)} part(s) written",
        )

    def health(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, available=self.is_configured())


# ---------------------------------------------------------------------------
# llm
# ---------------------------------------------------------------------------
@dataclass
class LLMOutcome:
    """Result of a structured LLM call."""

    data: Optional[Dict[str, Any]]
    provider: str
    model: str
    success: bool
    mode: str = "live"
    detail: Optional[str] = None
    latency_ms: Optional[int] = None
    raw_text: Optional[str] = None


class LLMProvider(abc.ABC):
    """Structured (schema-constrained) text generation."""

    name: str = "llm"

    @abc.abstractmethod
    def is_configured(self) -> bool: ...

    @abc.abstractmethod
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: Type[BaseModel],
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMOutcome:
        """Return data matching ``schema``.

        ``context`` carries the already-structured evidence (incident,
        memory_evidence). Text providers may append it to the prompt; the
        deterministic provider consumes it directly instead of re-parsing text.
        Never raises: on failure returns ``success=False``.
        """

    def health(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, available=self.is_configured())


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------
@dataclass
class ActionOutcome:
    """Result of a *simulated* action. There is intentionally no real-execute
    method anywhere in this codebase."""

    success: bool
    action_type: str
    message: str
    duration_seconds: float
    telemetry: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = "Simulated only. No production system was contacted."


class ActionProvider(abc.ABC):
    """The action layer. Simulated and human-approved by construction."""

    name: str = "action"

    @abc.abstractmethod
    def is_configured(self) -> bool: ...

    @abc.abstractmethod
    def execute_simulated(
        self,
        *,
        incident_id: str,
        action: str,
        action_type: str,
        context: Dict[str, Any],
    ) -> ActionOutcome: ...
