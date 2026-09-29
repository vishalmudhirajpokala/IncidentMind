"""Metrics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.system import MetricsOverview
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/overview",
    response_model=MetricsOverview,
    summary="Counts derived from the database",
    description=(
        "Every figure is counted from real rows. There are no synthetic "
        "improvement percentages and no benchmark claims in this response."
    ),
)
def overview(session: Session = Depends(get_session)) -> MetricsOverview:
    return MetricsService(session).overview()
