"""Memory routes: recall, recent retained experiences, provider status."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.integrations.relevance import QueryProfile, score_relevance
from app.schemas.memory import (
    MemoryEventRead,
    MemoryRecallResponse,
    ProviderStatus,
)
from app.services.agent_service import AgentService
from app.services.memory_service import MemoryService, build_recall_query

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post(
    "/recall",
    response_model=MemoryRecallResponse,
    summary="Recall historical experience for an incident",
    description=(
        "Builds a specific multi-facet query from the incident (service, symptoms, "
        "signals, change, context, failure pattern) and recalls relevant resolved "
        "incidents from organisational memory. Use /memory/relevance for a free-text "
        "probe."
    ),
    responses={404: {"description": "Incident not found"}},
)
def recall(
    incident_id: str = Body(..., embed=True, description="Incident to recall memory for"),
    limit: int = Query(5, ge=1, le=50),
    session: Session = Depends(get_session),
) -> MemoryRecallResponse:
    agent = AgentService(session)
    incident = agent._load(incident_id)  # 404 if missing
    memory = MemoryService(session)
    response, _evidence, _status = memory.recall(incident, limit=limit)
    return response


@router.post(
    "/relevance",
    summary="Score a free-text query against stored experience",
    description=(
        "Transparent view of the local lexical relevance function. Useful for "
        "debugging why a memory was or was not retrieved."
    ),
)
def relevance(
    query: str = Body(..., embed=True, min_length=3),
    service: Optional[str] = Body(None, embed=True),
    limit: int = Query(5, ge=1, le=50),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    memory = MemoryService(session)
    incident_like: Dict[str, Any] = {
        "title": query,
        "description": query,
        "service": service or "",
        "signals": [],
        "metrics": {},
    }
    profile = QueryProfile.from_incident(incident_like)
    results = memory.provider.recall(query, limit=limit, incident=incident_like)  # type: ignore[call-arg]
    return {
        "query": query,
        "method": "local_lexical_overlap",
        "note": (
            "This is a transparent keyword-overlap score computed locally. It is not a "
            "semantic similarity and is never presented as one."
        ),
        "count": len(results),
        "matches": [
            {
                "memory_id": r.id,
                "score": r.score,
                "matched_on": (r.raw or {}).get("matched_on", []),
                "why_relevant": (r.raw or {}).get("why_relevant"),
            }
            for r in results
        ],
    }


@router.get(
    "/recent",
    response_model=List[MemoryEventRead],
    summary="Recently retained experiences",
)
def recent(
    limit: int = Query(20, ge=1, le=200),
    incident_id: Optional[str] = Query(None, description="Filter to one incident"),
    session: Session = Depends(get_session),
) -> List[MemoryEventRead]:
    return MemoryService(session).recent(limit=limit, incident_id=incident_id)


@router.get(
    "/status",
    response_model=ProviderStatus,
    summary="Memory provider health",
    description=(
        "Reports which memory provider is active. mode is 'live' when a real "
        "external service answered, 'demo' when the local mirror is serving, and "
        "'unavailable' when no provider is configured."
    ),
)
def memory_status(session: Session = Depends(get_session)) -> ProviderStatus:
    return MemoryService(session).health()
