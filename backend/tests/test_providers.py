"""Provider behaviour, including total failure of every external dependency.

These tests pin the most important promise of the design: when Hindsight or
the LLM is unreachable, requests still succeed and the response says plainly
which provider answered. Nothing is fabricated to cover a gap.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import Settings
from app.integrations.base import MemoryProvider, RetrievedMemory
from app.integrations.deterministic_provider import DeterministicLLMProvider, classify_pattern
from app.integrations.groq_provider import GroqLLMProvider, extract_json
from app.integrations.hindsight_provider import HindsightMemoryProvider
from app.integrations.relevance import QueryProfile, score_relevance, version_family
from app.models.incident import Incident
from app.schemas.llm import LLMInvestigation
from app.schemas.memory import RetainRequest
from app.services.memory_service import MemoryService

# A port nothing is listening on. Connections fail fast.
DEAD = "http://127.0.0.1:9"

INCIDENT = Incident(
    id="INC-TEST-1",
    title="Pool exhaustion after release",
    service="checkout-api",
    severity="high",
    description="Database connection pool exhausted after deploying v2.8.1.",
    signals=["error rate 18%", "pool 96%"],
    metrics={"error_rate": 18.0},
    deployment_version="v2.8.1",
)


def _offline_settings(**overrides) -> Settings:
    base = {
        "HINDSIGHT_BASE_URL": DEAD,
        "HINDSIGHT_API_KEY": "not-a-real-key",
        "MEMORY_PROVIDER": "auto",
        "GROQ_API_KEY": "not-a-real-key",
        "LLM_PROVIDER": "auto",
        "HINDSIGHT_TIMEOUT_SECONDS": 1.0,
        "LLM_TIMEOUT_SECONDS": 1.0,
    }
    base.update(overrides)
    return Settings(**base)


# ------------------------------------------------------------ hindsight down
def test_hindsight_recall_returns_empty_instead_of_raising() -> None:
    provider = HindsightMemoryProvider(_offline_settings())
    assert provider.is_configured() is True
    assert provider.recall("anything") == []


def test_hindsight_retain_reports_failure_instead_of_raising() -> None:
    outcome = HindsightMemoryProvider(_offline_settings()).retain("some content")
    assert outcome.success is False
    assert outcome.external is False
    assert outcome.detail


def test_hindsight_health_reports_unavailable_without_raising() -> None:
    status = HindsightMemoryProvider(_offline_settings()).health()
    assert status.available is False
    assert status.name == "hindsight"


def test_hindsight_unconfigured_is_not_live() -> None:
    settings = _offline_settings(HINDSIGHT_BASE_URL="", HINDSIGHT_API_KEY="")
    provider = HindsightMemoryProvider(settings)
    assert provider.is_configured() is False
    assert provider.recall("anything") == []
    assert provider.health().mode == "unavailable"


def test_memory_service_falls_back_to_local_when_hindsight_is_down(session: Session) -> None:
    settings = _offline_settings()
    service = MemoryService(session, settings)
    assert service.provider.name == "hindsight"
    assert service.fallback is not None

    response, evidence, status = service.recall(INCIDENT)
    # Degraded, but functional: the request completed and reported honestly
    # that the primary provider did not answer.
    assert response.count == 0
    assert response.status in {"empty", "degraded"}
    assert evidence == []
    assert status.name == "hindsight"
    assert status.available is False


def test_retain_survives_a_dead_hindsight(session: Session) -> None:
    settings = _offline_settings()
    service = MemoryService(session, settings)
    request = RetainRequest(
        incident_id=INCIDENT.id,
        service="checkout-api",
        symptoms="Pool exhausted",
        signals=["error rate 18%"],
        metrics={"error_rate": 18.0},
        deployment="v2.8.1",
        investigation=["Checked pool telemetry"],
        root_cause="Connection leak",
        actions_tried=["Restart"],
        successful_action="Rolled back to v2.8.0",
        failed_action="Restart did not help",
        outcome="Recovered",
        resolution_time="272 seconds",
        lesson="Roll back on pool saturation after a release",
    )
    response = service.retain(INCIDENT, request)

    # The write lands in the local mirror and says so.
    assert response.success is True
    assert response.external_retained is False
    assert response.status == "retained_locally"
    assert response.memory_event_id


# ------------------------------------------------------------------- llm down
def test_groq_returns_failure_instead_of_raising() -> None:
    provider = GroqLLMProvider(_offline_settings())
    outcome = provider.complete_json(system="s", user="u", schema=LLMInvestigation)
    assert outcome.success is False
    assert outcome.data is None
    assert outcome.detail


def test_groq_health_reports_unavailable() -> None:
    status = GroqLLMProvider(_offline_settings()).health()
    assert status.available is False


def test_agent_falls_back_to_the_deterministic_analyst(session: Session) -> None:
    """With Groq pinned but dead, the request still produces a real analysis."""
    from app.services.agent_service import AgentService

    incident = Incident(
        id="INC-TEST-2",
        title="Pool exhaustion after release",
        service="checkout-api",
        severity="high",
        description="Database connection pool exhausted after deploying v2.8.1.",
        signals=["error rate 18%"],
        metrics={"error_rate": 18.0},
        deployment_version="v2.8.1",
        status="active",
    )
    session.add(incident)
    session.commit()

    agent = AgentService(session, _offline_settings(LLM_PROVIDER="groq"))
    result = agent.investigate(incident.id, memory_enabled=True)

    assert result.summary
    assert result.recommended_action is not None
    assert result.llm_provider is not None
    # groq was tried and failed; the fallback is named in the response.
    assert result.llm_provider.available is True
    assert result.llm_provider.detail


def test_api_investigation_survives_every_provider_failing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recall that blows up must not become a 500."""

    class ExplodingProvider(MemoryProvider):
        name = "exploding"

        def is_configured(self) -> bool:
            return True

        def recall(self, query: str, *, limit: int = 5):
            raise RuntimeError("memory service on fire")

        def retain(self, content, **kwargs):
            raise RuntimeError("memory service on fire")

    def broken_factory(session, settings=None):
        return ExplodingProvider(), None, "live"

    monkeypatch.setattr("app.services.memory_service.get_memory_provider", broken_factory)

    incident_id = client.post(
        "/api/incidents",
        json={"title": "Failure isolation probe", "service": "probe", "description": "x"},
    ).json()["id"]

    response = client.post(f"/api/incidents/{incident_id}/investigate", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["memory_count"] == 0
    assert body["summary"]
    assert "on fire" in (body["memory_detail"] or "")


# --------------------------------------------------------- provider selection
def test_factory_selection_rules() -> None:
    from app.integrations.factory import get_llm_provider, get_memory_provider

    with Session(_engine()) as db:
        primary, fallback, mode = get_memory_provider(db, _offline_settings(HINDSIGHT_BASE_URL="", HINDSIGHT_API_KEY=""))
        assert primary.name == "local"
        assert fallback is None
        assert mode == "demo"

        primary, fallback, mode = get_memory_provider(db, _offline_settings(MEMORY_PROVIDER="local"))
        assert primary.name == "local" and fallback is None

        primary, fallback, mode = get_memory_provider(db, _offline_settings(MEMORY_PROVIDER="hindsight"))
        assert primary.name == "hindsight" and fallback is not None

    provider, fallback, mode = get_llm_provider(_offline_settings(GROQ_API_KEY=""))
    assert provider.name == "deterministic" and fallback is None and mode == "demo"

    provider, fallback, mode = get_llm_provider(_offline_settings(LLM_PROVIDER="groq"))
    assert provider.name == "groq" and fallback is not None

    provider, _fallback, mode = get_llm_provider(_offline_settings(LLM_PROVIDER="mock"))
    assert provider.name == "deterministic" and mode == "demo"


def _engine():
    from app.database import engine

    return engine


# ------------------------------------------------------------- offline pieces
def test_deterministic_analyst_never_raises_on_odd_input() -> None:
    provider = DeterministicLLMProvider()
    outcome = provider.complete_json(
        system="s",
        user="u",
        schema=LLMInvestigation,
        context={"incident": {}, "memory_evidence": []},
    )
    assert outcome.success is True
    result = LLMInvestigation.model_validate(outcome.data)
    assert result.recommended_action is not None
    assert result.recommended_action.requires_approval is True


def test_deterministic_analyst_keeps_confidence_low_without_memory() -> None:
    provider = DeterministicLLMProvider()
    with_memory = provider.complete_json(
        system="s",
        user="u",
        schema=LLMInvestigation,
        context={
            "incident": {
                "service": "checkout-api",
                "deployment_version": "v2.8.1",
                "description": "connection pool exhausted",
            },
            "memory_evidence": [
                {
                    "source_incident_id": "INC-001",
                    "historical_root_cause": "Connection leak",
                    "historical_action": "Rolled back to v2.8.0",
                    "historical_outcome": "Recovered",
                    "why_relevant": "same service",
                    "relevance": 0.8,
                }
            ],
        },
    )
    without_memory = provider.complete_json(
        system="s",
        user="u",
        schema=LLMInvestigation,
        context={
            "incident": {
                "service": "checkout-api",
                "deployment_version": "v2.8.1",
                "description": "connection pool exhausted",
            },
            "memory_evidence": [],
        },
    )
    assert with_memory.data["hypotheses"][0]["confidence"] > without_memory.data["hypotheses"][0]["confidence"]
    # Empty evidence with no `memory_enabled` flag means memory was searched and
    # found nothing. That must be reported as a search, not as an absence.
    limitations = without_memory.data["limitations"].lower()
    assert "searched" in limitations
    assert "withheld" not in limitations


def test_deterministic_analyst_distinguishes_withheld_from_empty_memory() -> None:
    """Memory OFF must not be reported as 'no experience exists'."""
    provider = DeterministicLLMProvider()
    base_context = {
        "incident": {
            "service": "checkout-api",
            "deployment_version": "v2.8.1",
            "description": "connection pool exhausted",
        },
        "memory_evidence": [],
    }

    searched = provider.complete_json(
        system="s", user="u", schema=LLMInvestigation, context=base_context
    )
    withheld = provider.complete_json(
        system="s",
        user="u",
        schema=LLMInvestigation,
        context={**base_context, "memory_enabled": False},
    )

    assert "searched" in searched.data["limitations"].lower()
    assert "withheld" in withheld.data["limitations"].lower()
    assert "no relevant historical experience exists" not in (
        withheld.data["limitations"].lower()
    )
    # The control run must not pretend history informed it.
    assert "memory" in withheld.data["reasoning_summary"].lower()


def test_json_extraction_handles_awkward_model_output() -> None:
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Here you go:\n{"a": 1}\nHope that helps!') == {"a": 1}
    assert extract_json('{"a": 1,}') == {"a": 1}
    assert extract_json("no json at all") is None
    assert extract_json("") is None


def test_relevance_never_attributes_a_score_to_hindsight() -> None:
    profile = QueryProfile.from_incident(
        {"service": "checkout-api", "description": "pool exhausted", "signals": [], "metrics": {}}
    )
    result = score_relevance(profile, {"service": "checkout-api", "symptoms": "pool exhausted"})
    assert result.score > 0
    assert result.method == "local_lexical_overlap"


def test_version_family_extraction() -> None:
    assert version_family("v2.8.3") == "2.8"
    assert version_family("2.10.1") == "2.10"
    assert version_family("no version") is None
    assert version_family(None) is None


def test_classify_pattern_is_specificity_ordered() -> None:
    # A pool problem that also mentions latency and 503s is still a pool problem.
    rule = classify_pattern(
        {
            "description": "503s up, latency tripled, database connection pool exhausted",
            "title": "",
            "signals": [],
            "metrics": {},
        }
    )
    assert rule and rule["id"] == "db_pool"


def test_classify_pattern_returns_none_for_unclassifiable() -> None:
    assert classify_pattern({"description": "the logo looks wrong", "signals": [], "metrics": {}}) is None


def test_retrieved_memory_carries_no_invented_score() -> None:
    memory = RetrievedMemory(id="m1", text="t", provider="hindsight", score=None)
    assert memory.score is None
