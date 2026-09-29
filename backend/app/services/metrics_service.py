"""Metrics derived from the database.

Every figure here is counted from real rows. There are no hard-coded
percentages, no synthetic "before/after improvement" figures and no benchmark
claims: the endpoint reports what happened in this deployment and nothing else.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from sqlmodel import Session

from app.integrations.factory import get_llm_provider, get_memory_provider
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import ProviderStatus
from app.schemas.system import MetricsOverview
from app.utils.logging import get_logger

log = get_logger("services.metrics")


class MetricsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.incidents = IncidentRepository(session)
        self.investigations = InvestigationRepository(session)
        self.memories = MemoryRepository(session)

    def overview(self) -> MetricsOverview:
        incidents = self.incidents.all()
        runs = self.investigations.all(limit=10_000)
        events = self.memories.all_experiences()

        by_severity = Counter(i.severity for i in incidents)
        by_service = Counter(i.service for i in incidents)

        external = sum(1 for e in events if e.external_retained)

        # Mean time to resolve, over incidents that actually recorded one.
        # Incidents still open, or resolved without a measured duration, are
        # excluded rather than counted as zero - that would understate the mean
        # and is exactly the kind of flattering number this endpoint avoids.
        durations = [
            float(i.resolution_time_seconds)
            for i in incidents
            if i.resolution_time_seconds is not None
        ]
        average_resolution = (
            round(sum(durations) / len(durations), 1) if durations else None
        )

        providers: Dict[str, ProviderStatus] = {}
        try:
            memory_provider, _fallback, _mode = get_memory_provider(self.session)
            providers["memory"] = memory_provider.health()
        except Exception as exc:  # noqa: BLE001
            providers["memory"] = ProviderStatus(
                name="memory", mode="unavailable", available=False, detail=type(exc).__name__
            )
        try:
            llm_provider, _fallback, _mode = get_llm_provider()
            providers["llm"] = llm_provider.health()
        except Exception as exc:  # noqa: BLE001
            providers["llm"] = ProviderStatus(
                name="llm", mode="unavailable", available=False, detail=type(exc).__name__
            )

        return MetricsOverview(
            incidents_total=len(incidents),
            incidents_active=sum(1 for i in incidents if i.status != "resolved"),
            incidents_resolved=sum(1 for i in incidents if i.status == "resolved"),
            by_severity=dict(by_severity),
            by_service=dict(by_service),
            investigations_total=len(runs),
            investigations_memory_on=sum(1 for r in runs if r.mode == "memory_on"),
            investigations_memory_off=sum(1 for r in runs if r.mode == "memory_off"),
            memory_events_total=len(events),
            memory_events_external=external,
            memory_events_local_only=len(events) - external,
            average_confidence_memory_on=self.investigations.average_confidence("memory_on"),
            average_confidence_memory_off=self.investigations.average_confidence("memory_off"),
            average_resolution_time_seconds=average_resolution,
            incidents_with_measured_resolution=len(durations),
            providers=providers,
        )

    def memory_count_by_incident(self) -> Dict[str, int]:
        counter: Counter = Counter()
        for event in self.memories.all_experiences():
            if event.incident_id:
                counter[event.incident_id] += 1
        return dict(counter)
