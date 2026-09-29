"""Groq LLM provider (LIVE path).

Calls the Groq OpenAI-compatible chat completions endpoint and coerces the reply
into a Pydantic model. Robustness rules, in order:

  1. ask for JSON explicitly and set ``response_format={"type": "json_object"}``
  2. extract JSON defensively (fenced blocks, leading prose, trailing commas)
  3. validate with the supplied Pydantic schema
  4. retry once on failure with a stricter instruction
  5. if it still fails, return ``success=False`` and let the caller fall back

It never raises, so a dead LLM degrades the response instead of 500-ing.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings, settings as default_settings
from app.integrations.base import LLMOutcome, LLMProvider
from app.schemas.memory import ProviderStatus
from app.utils.logging import get_logger

log = get_logger("integrations.groq")

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of a single JSON object from model output."""
    if not text:
        return None

    candidates = []
    fenced = _FENCE_RE.search(text)
    if fenced:
        candidates.append(fenced.group(1))
    candidates.append(text)

    # Also try the outermost {...} span.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        cleaned = _TRAILING_COMMA_RE.sub(r"\1", candidate).strip()
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


class GroqLLMProvider(LLMProvider):
    """Live LLM provider backed by Groq."""

    name = "groq"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or default_settings
        self._client: Optional[httpx.Client] = None

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.settings.GROQ_BASE_URL.rstrip("/"),
                timeout=self.settings.LLM_TIMEOUT_SECONDS,
            )
        return self._client

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return self.settings.llm_configured

    # ------------------------------------------------------------ internals
    def _post_chat(self, system: str, user: str, strict: bool) -> str:
        instruction = system
        if strict:
            instruction = (
                system
                + "\n\nIMPORTANT: respond with raw JSON only. No markdown fences, "
                "no commentary before or after the JSON object."
            )

        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.LLM_TEMPERATURE,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }
        response = self._http().post("/chat/completions", headers=self._headers(), json=payload)
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"] or ""

    # -------------------------------------------------------------- public
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: Type[BaseModel],
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMOutcome:
        if not self.is_configured():
            return LLMOutcome(
                data=None,
                provider=self.name,
                model=self.settings.LLM_MODEL,
                success=False,
                mode="live",
                detail="GROQ_API_KEY not set",
            )

        # Structured evidence is appended so the model can cite it verbatim.
        if context:
            user = f"{user}\n\nSTRUCTURED EVIDENCE (JSON):\n{json.dumps(context, default=str)}"

        attempts = max(1, self.settings.LLM_RETRIES + 1)
        last_error = "unknown"
        started = time.perf_counter()

        for attempt in range(attempts):
            try:
                raw_text = self._post_chat(system, user, strict=(attempt > 0))
                parsed = extract_json(raw_text)
                if parsed is None:
                    last_error = "no JSON object found in model output"
                    continue
                validated = schema.model_validate(parsed)
                latency = int((time.perf_counter() - started) * 1000)
                log.info(
                    "groq structured completion",
                    extra={
                        "event_provider": self.name,
                        "event_model": self.settings.LLM_MODEL,
                        "event_attempt": attempt + 1,
                        "event_latency_ms": latency,
                    },
                )
                return LLMOutcome(
                    data=validated.model_dump(),
                    provider=self.name,
                    model=self.settings.LLM_MODEL,
                    success=True,
                    mode="live",
                    latency_ms=latency,
                    raw_text=raw_text,
                )
            except ValidationError as exc:
                last_error = f"schema validation failed: {exc.error_count()} error(s)"
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"

            log.warning(
                "groq attempt failed",
                extra={"event_provider": self.name, "event_attempt": attempt + 1, "event_error": last_error},
            )

        return LLMOutcome(
            data=None,
            provider=self.name,
            model=self.settings.LLM_MODEL,
            success=False,
            mode="live",
            detail=last_error,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def health(self) -> ProviderStatus:
        if not self.is_configured():
            return ProviderStatus(
                name=self.name, mode="unavailable", available=False, detail="GROQ_API_KEY not set"
            )
        started = time.perf_counter()
        try:
            response = self._http().get("/models", headers=self._headers())
            latency = int((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            return ProviderStatus(
                name=self.name, mode="live", available=True, detail=self.settings.LLM_MODEL, latency_ms=latency
            )
        except Exception as exc:  # noqa: BLE001
            return ProviderStatus(
                name=self.name,
                mode="live",
                available=False,
                detail=type(exc).__name__,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
