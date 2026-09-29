"""Hindsight memory provider (LIVE path).

Endpoint shapes are taken from the official Hindsight HTTP API (v0.10.x):

    POST {base}{prefix}/banks/{bank_id}/memories/recall
        -> {"results": [{"id", "text", "type", "context", "entities",
                         "occurred_start", "occurred_end", "chunk_id"}],
            "trace": {"num_results", "query", "time_seconds"}}

    POST {base}{prefix}/banks/{bank_id}/memories
        -> {"success": bool, "bank_id": str, "items_count": int, "async": bool}

    POST {base}{prefix}/banks/{bank_id}/reflect
        -> {"text": str, "based_on": {...}, "structured_output": {...}}

Two things this adapter deliberately does NOT do:

  * It never invents a similarity score. ``recall`` in Hindsight returns no
    score, so ``RetrievedMemory.score`` is left as ``None`` and the caller
    computes a local relevance figure and labels it as locally computed.
  * It never raises on transport failure. Errors are captured and surfaced
    through ``health()`` / logs so the request degrades instead of 500-ing.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import Settings, settings as default_settings
from app.integrations.base import MemoryProvider, RetrievedMemory, RetainOutcome
from app.schemas.memory import ProviderStatus
from app.utils.logging import get_logger

log = get_logger("integrations.hindsight")

# Fact types we want back from Hindsight. "experience" covers resolved
# incidents and the actions taken during them.
RECALL_TYPES = ["experience", "observation", "world"]


class HindsightMemoryProvider(MemoryProvider):
    """Talks to a real Hindsight deployment over HTTP."""

    name = "hindsight"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or default_settings
        self._client: Optional[httpx.Client] = None
        self._last_error: Optional[str] = None

    # ------------------------------------------------------------------ util
    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.settings.HINDSIGHT_BASE_URL.rstrip("/"),
                timeout=self.settings.HINDSIGHT_TIMEOUT_SECONDS,
            )
        return self._client

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.HINDSIGHT_API_KEY:
            headers["Authorization"] = f"Bearer {self.settings.HINDSIGHT_API_KEY}"
        return headers

    def _bank_path(self, suffix: str) -> str:
        prefix = self.settings.HINDSIGHT_API_PREFIX.strip("/")
        bank = self.settings.HINDSIGHT_BANK_ID
        return f"/{prefix}/banks/{bank}/{suffix}"

    def _fail(self, exc: Exception) -> None:
        # httpx exception str() can embed the URL; it never contains the key.
        self._last_error = f"{type(exc).__name__}: {exc}"
        log.warning(
            "hindsight request failed",
            extra={"event_provider": self.name, "event_error": self._last_error},
        )

    # ----------------------------------------------------------------- read
    def is_configured(self) -> bool:
        return self.settings.hindsight_configured

    def recall(self, query: str, *, limit: int = 5) -> List[RetrievedMemory]:
        if not self.is_configured():
            return []

        payload: Dict[str, Any] = {
            "query": query,
            "types": RECALL_TYPES,
            "budget": self.settings.HINDSIGHT_RECALL_BUDGET,
            "max_tokens": self.settings.HINDSIGHT_RECALL_MAX_TOKENS,
        }

        try:
            response = self._http().post(
                self._bank_path("memories/recall"),
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:  # noqa: BLE001 - must not break the request
            self._fail(exc)
            return []

        results = body.get("results") or []
        log.info(
            "hindsight recall",
            extra={
                "event_provider": self.name,
                "event_result_count": len(results),
                "event_num_results": (body.get("trace") or {}).get("num_results"),
            },
        )

        memories: List[RetrievedMemory] = []
        for index, item in enumerate(results[:limit]):
            if not isinstance(item, dict):
                continue
            memories.append(
                RetrievedMemory(
                    id=str(item.get("id") or f"hindsight-{index}"),
                    text=str(item.get("text") or ""),
                    context=item.get("context"),
                    fact_type=item.get("type"),
                    occurred_start=item.get("occurred_start"),
                    entities=list(item.get("entities") or []),
                    # Hindsight returns no similarity score. Left as None on purpose.
                    score=None,
                    provider=self.name,
                    raw=item,
                )
            )
        return memories

    def reflect(self, query: str, *, response_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call Hindsight's reflect endpoint for a synthesised answer.

        Used opportunistically for the reasoning summary; callers must treat
        failure as non-fatal.
        """
        if not self.is_configured():
            return {}

        payload: Dict[str, Any] = {"query": query, "budget": "low"}
        if response_schema:
            payload["response_schema"] = response_schema

        try:
            response = self._http().post(
                self._bank_path("reflect"),
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return {}

    # ---------------------------------------------------------------- write
    def retain(
        self,
        content: str,
        *,
        context: str = "",
        document_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ) -> RetainOutcome:
        if not self.is_configured():
            return RetainOutcome(
                success=False,
                provider=self.name,
                external=False,
                detail="Hindsight is not configured",
            )

        item: Dict[str, Any] = {"content": content}
        if context:
            item["context"] = context
        if document_id:
            item["document_id"] = document_id
        if tags:
            item["tags"] = tags
        if timestamp:
            item["timestamp"] = timestamp

        try:
            response = self._http().post(
                self._bank_path("memories"),
                headers=self._headers(),
                json={"items": [item], "async": self.settings.HINDSIGHT_RETAIN_ASYNC},
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return RetainOutcome(
                success=False,
                provider=self.name,
                external=False,
                detail=self._last_error,
            )

        success = bool(body.get("success", False))
        # The retain response reports items_count, not the created memory ids,
        # so external_ids is intentionally left empty rather than invented.
        log.info(
            "hindsight retain",
            extra={
                "event_provider": self.name,
                "event_success": success,
                "event_items_count": body.get("items_count"),
            },
        )
        return RetainOutcome(
            success=success,
            provider=self.name,
            external=True,
            external_ids=[],
            detail=(
                f"retained {body.get('items_count')} item(s) to bank "
                f"{body.get('bank_id') or self.settings.HINDSIGHT_BANK_ID}"
            ),
        )

    def retain_batch(
        self,
        items: List[Dict[str, Any]],
        *,
        document_id: Optional[str] = None,
    ) -> RetainOutcome:
        """Write several labelled parts of one experience in a single request.

        Each part carries the same ``context`` marker so recall can group the
        extracted facts back into a single reconstructable experience.
        """
        if not self.is_configured():
            return RetainOutcome(
                success=False,
                provider=self.name,
                external=False,
                detail="Hindsight is not configured",
            )

        payload_items: List[Dict[str, Any]] = []
        for item in items:
            content = item.get("content")
            if not content:
                continue
            payload_item: Dict[str, Any] = {"content": str(content)}
            if item.get("context"):
                payload_item["context"] = str(item["context"])
            if document_id:
                payload_item["document_id"] = document_id
            if item.get("tags"):
                payload_item["tags"] = list(item["tags"])
            if item.get("timestamp"):
                payload_item["timestamp"] = item["timestamp"]
            payload_items.append(payload_item)

        if not payload_items:
            return RetainOutcome(
                success=False, provider=self.name, external=False, detail="nothing to retain"
            )

        try:
            response = self._http().post(
                self._bank_path("memories"),
                headers=self._headers(),
                json={"items": payload_items, "async": self.settings.HINDSIGHT_RETAIN_ASYNC},
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return RetainOutcome(
                success=False, provider=self.name, external=False, detail=self._last_error
            )

        success = bool(body.get("success", False))
        log.info(
            "hindsight retain_batch",
            extra={
                "event_provider": self.name,
                "event_success": success,
                "event_items_count": body.get("items_count"),
                "event_sent": len(payload_items),
            },
        )
        return RetainOutcome(
            success=success,
            provider=self.name,
            external=True,
            external_ids=[],
            detail=(
                f"wrote {body.get('items_count')} item(s) to bank "
                f"{body.get('bank_id') or self.settings.HINDSIGHT_BANK_ID}"
            ),
        )

    # --------------------------------------------------------------- health
    def health(self) -> ProviderStatus:
        if not self.is_configured():
            return ProviderStatus(
                name=self.name,
                mode="unavailable",
                available=False,
                detail="HINDSIGHT_BASE_URL / HINDSIGHT_API_KEY not set",
            )
        started = time.perf_counter()
        try:
            response = self._http().get("/health", headers=self._headers())
            latency = int((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            return ProviderStatus(
                name=self.name,
                mode="live",
                available=True,
                detail=f"bank={self.settings.HINDSIGHT_BANK_ID}",
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return ProviderStatus(
                name=self.name,
                mode="live",
                available=False,
                detail=f"{type(exc).__name__}",
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
