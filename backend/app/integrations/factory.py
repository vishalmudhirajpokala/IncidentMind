"""Provider selection.

This is the only place that decides which concrete implementation runs. Service
code asks for a provider by capability and never branches on vendor specifics,
which is what keeps the LIVE path and the DEMO path interchangeable.

Selection rules:
  * MEMORY_PROVIDER=auto  -> Hindsight when configured, otherwise the local mirror
  * MEMORY_PROVIDER=hindsight -> Hindsight only; a failure degrades to local
  * MEMORY_PROVIDER=local -> local mirror only
  * LLM_PROVIDER=auto     -> Groq when configured, otherwise the deterministic analyst
  * LLM_PROVIDER=groq     -> Groq only, falling back to deterministic on failure
  * LLM_PROVIDER=mock     -> deterministic only
"""

from __future__ import annotations

from typing import Optional, Tuple

from sqlmodel import Session

from app.config import Settings, settings as default_settings
from app.integrations.action_provider import SimulatedActionProvider
from app.integrations.base import ActionProvider, LLMProvider, MemoryProvider
from app.integrations.deterministic_provider import DeterministicLLMProvider
from app.integrations.groq_provider import GroqLLMProvider
from app.integrations.hindsight_provider import HindsightMemoryProvider
from app.integrations.local_memory_provider import LocalMemoryProvider


def get_memory_provider(
    session: Session, settings: Optional[Settings] = None
) -> Tuple[MemoryProvider, Optional[MemoryProvider], str]:
    """Return ``(primary, fallback, mode)`` for memory access.

    ``fallback`` is ``None`` when the primary cannot fail over (for example when
    the operator explicitly pinned the local provider).
    """
    settings = settings or default_settings
    choice = (settings.MEMORY_PROVIDER or "auto").lower()
    local = LocalMemoryProvider(session)

    if choice == "local":
        return local, None, "demo"
    if choice == "hindsight":
        return HindsightMemoryProvider(settings), local, "live"
    # auto
    if settings.hindsight_configured:
        return HindsightMemoryProvider(settings), local, "live"
    return local, None, "demo"


def get_llm_provider(
    settings: Optional[Settings] = None,
) -> Tuple[LLMProvider, Optional[LLMProvider], str]:
    """Return ``(primary, fallback, mode)`` for structured generation."""
    settings = settings or default_settings
    choice = (settings.LLM_PROVIDER or "auto").lower()
    deterministic = DeterministicLLMProvider()

    if choice == "mock":
        return deterministic, None, "demo"
    if choice == "groq":
        return GroqLLMProvider(settings), deterministic, "live"
    if settings.llm_configured:
        return GroqLLMProvider(settings), deterministic, "live"
    return deterministic, None, "demo"


def get_action_provider() -> ActionProvider:
    """The action layer. Always simulated; there is no real-execution variant."""
    return SimulatedActionProvider()
