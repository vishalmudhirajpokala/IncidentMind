"""Local memory provider (DEMO / fallback path).

Reads and writes the SQLite mirror of organisational memory. This is what makes
Demo Mode work with no external service: the same recall/retain interface is
implemented, results are clearly labelled ``local``, and the relevance figure
shown to the user is the transparent lexical score from
``app.integrations.relevance`` - never presented as a semantic similarity.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlmodel import Session

from app.integrations.base import MemoryProvider, RetrievedMemory, RetainOutcome
from app.integrations.relevance import QueryProfile, explain, score_relevance
from app.models.memory import MemoryEvent
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import ProviderStatus


class LocalMemoryProvider(MemoryProvider):
    """SQLite-backed memory provider used for demo mode and as a fallback."""

    name = "local"

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = MemoryRepository(session)

    def is_configured(self) -> bool:
        return True

    # ------------------------------------------------------------------ read
    def recall(self, query: str, *, limit: int = 5, incident: Optional[Dict[str, Any]] = None) -> List[RetrievedMemory]:
        """Return the most relevant stored experiences for this incident.

        Ranks by local lexical relevance against every stored experience and
        returns the top ``limit``. Returns an empty list when nothing clears a
        minimal relevance floor, so "no relevant history" stays a real answer.
        """
        if incident is None:
            # A bare query with no incident context: fall back to most recent.
            return self.repo.most_recent(limit=limit)

        profile = QueryProfile.from_incident(incident)
        candidates = self.repo.all_experiences()

        scored = []
        for event in candidates:
            document = {**event.event_metadata, "content": event.content}
            result = score_relevance(profile, document)
            if result.score <= 0.0:
                continue
            scored.append((result.score, result.matched_on, event))

        scored.sort(key=lambda item: (-item[0], item[2].retained_at), reverse=False)
        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RetrievedMemory(
                id=event.id,
                text=event.content or event.symptoms or event.title or "",
                context=event.title,
                fact_type=event.event_type,
                occurred_start=event.retained_at.isoformat() if event.retained_at else None,
                entities=[event.incident_id] if event.incident_id else [],
                score=round(score, 4),
                provider=self.name,
                raw={
                    "matched_on": matched,
                    "why_relevant": explain(matched),
                    "relevance_method": "local_lexical_overlap",
                    "metadata": event.event_metadata,
                },
            )
            for score, matched, event in scored[:limit]
        ]

    # ----------------------------------------------------------------- write
    def retain(
        self,
        content: str,
        *,
        context: str = "",
        document_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ) -> RetainOutcome:
        event = self.repo.create(
            incident_id=document_id,
            event_type="experience",
            title=context or None,
            symptoms=content,
            content=content,
            metadata={"tags": tags or []},
        )
        return RetainOutcome(
            success=True,
            provider=self.name,
            external=False,
            external_ids=[event.id],
            detail="Stored in the local memory mirror",
        )

    def retain_batch(
        self,
        items: List[Dict[str, Any]],
        *,
        document_id: Optional[str] = None,
    ) -> RetainOutcome:
        """Store one local mirror record for the whole experience.

        The local mirror keeps the structured experience fields intact, so a
        single row is the right shape here even though the caller sends the
        experience as labelled parts (the external memory service needs those
        parts separately so it can extract facts from each one). When the caller
        supplies the structured metadata it is stored verbatim, which is what
        lets a later recall report the real root cause, action and outcome.
        """
        parts = [str(i.get("content", "")) for i in items if i.get("content")]
        if not parts:
            return RetainOutcome(
                success=False, provider=self.name, external=False, detail="nothing to retain"
            )

        first = items[0]
        structured: Dict[str, Any] = dict(first.get("metadata") or {})
        if not structured:
            # No structured payload: fall back to the labelled view so nothing
            # is silently lost.
            structured = {
                str(item["label"]): item.get("content")
                for item in items
                if item.get("label")
            }

        content = str(first.get("narrative") or "\n".join(parts))

        event = self.repo.create(
            incident_id=document_id,
            event_type="experience",
            title=str(first.get("title") or structured.get("title") or ""),
            symptoms=str(structured.get("symptoms") or content[:400]),
            content=content,
            metadata=structured,
            provider=self.name,
            external_retained=False,
        )
        return RetainOutcome(
            success=True,
            provider=self.name,
            external=False,
            external_ids=[event.id],
            detail="Stored in the local memory mirror",
        )

    def health(self) -> ProviderStatus:
        try:
            count = self.repo.count()
        except Exception as exc:  # noqa: BLE001
            return ProviderStatus(name=self.name, available=False, detail=type(exc).__name__)
        return ProviderStatus(
            name=self.name,
            mode="demo",
            available=True,
            detail=f"{count} experience(s) in local mirror",
        )
