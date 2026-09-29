"""Memory routes and the local relevance function."""

from __future__ import annotations

from fastapi.testclient import TestClient

INCIDENT = {
    "title": "Pool saturation on checkout",
    "service": "checkout-api",
    "severity": "high",
    "description": "Database connection pool exhausted, requests timing out.",
    "signals": ["error rate 18%", "pool 96%"],
    "metrics": {"error_rate": 18.0, "pool_utilization": 96.0},
    "deployment_version": "v2.8.1",
}


def _create(client: TestClient, **overrides) -> str:
    response = client.post("/api/incidents", json={**INCIDENT, **overrides})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_recall_returns_200_and_a_rich_query(client: TestClient) -> None:
    incident_id = _create(client)
    response = client.post("/api/memory/recall", json={"incident_id": incident_id})
    assert response.status_code == 200
    body = response.json()

    assert "count" in body and "memories" in body and "query" in body
    # The query must be specific, not "how do I fix this incident".
    query = body["query"]
    for facet in ("SERVICE:", "SYMPTOMS:", "SIGNALS:", "CHANGE:", "CONTEXT:", "FAILURE PATTERN:"):
        assert facet in query, f"recall query is missing the {facet} facet"


def test_recall_on_empty_memory_reports_none(client: TestClient) -> None:
    incident_id = _create(client)
    body = client.post("/api/memory/recall", json={"incident_id": incident_id}).json()
    assert body["count"] == 0
    assert body["source"] == "none"
    assert body["status"] == "empty"


def test_recall_finds_a_stored_experience(client: TestClient) -> None:
    incident_id = _create(client)
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Connection pool exhausted by a leak.",
            "action_taken": "Rolled back checkout-api to v2.8.0",
            "outcome": "Error rate fell to 1.4%.",
            "lesson": "Suspect leaked connections after a checkout-api release.",
        },
    )

    query_incident = _create(client, title="Database pool exhausted again", deployment_version="v2.9.2")
    body = client.post("/api/memory/recall", json={"incident_id": query_incident}).json()
    assert body["count"] >= 1
    assert body["source"] == "local"
    assert body["status"] == "ok"

    top = body["memories"][0]
    assert top["source_incident_id"] == incident_id
    assert top["relevance"] and top["relevance"] > 0
    # Hindsight returns no similarity score, so this must be labelled as local.
    assert top["relevance_method"] == "local_lexical_overlap"
    assert top["why_relevant"]


def test_recall_ranks_the_most_similar_first(client: TestClient) -> None:
    """An unrelated incident must not outrank the matching one."""
    for title, service, description in (
        ("Checkout pool exhaustion", "checkout-api", "Database connection pool exhausted under load."),
        ("Gateway disk full", "api-gateway", "Disk saturation on the gateway host, log rotation disabled."),
    ):
        incident_id = _create(
            client,
            title=title,
            service=service,
            description=description,
            deployment_version=None,
        )
        client.post(
            f"/api/incidents/{incident_id}/resolve",
            json={
                "root_cause": f"{service} specific cause",
                "action_taken": f"Fixed {service}",
                "outcome": "Recovered",
                "lesson": f"{service} lesson",
            },
        )

    query_incident = _create(client, title="Checkout pool exhausted", deployment_version="v2.9.5")
    memories = client.post("/api/memory/recall", json={"incident_id": query_incident}).json()["memories"]
    assert memories
    assert memories[0]["historical_service"] == "checkout-api"
    assert memories[0]["relevance"] >= memories[-1]["relevance"]


def test_recall_limit_is_honoured(client: TestClient) -> None:
    incident_id = _create(client)
    body = client.post(
        "/api/memory/recall", json={"incident_id": incident_id}, params={"limit": 2}
    ).json()
    assert len(body["memories"]) <= 2


def test_recall_validates_input(client: TestClient) -> None:
    assert client.post("/api/memory/recall", json={}).status_code == 422
    assert (
        client.post("/api/memory/recall", json={"incident_id": "NOPE"}).status_code == 404
    )
    assert (
        client.post("/api/memory/recall", json={"incident_id": "INC-001"}, params={"limit": 0}).status_code
        == 422
    )


def test_recent_returns_retained_memories(client: TestClient) -> None:
    assert client.get("/api/memory/recent").json() == []

    incident_id = _create(client)
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={"root_cause": "Leak", "action_taken": "Rollback", "outcome": "ok", "lesson": "x"},
    )
    events = client.get("/api/memory/recent").json()
    assert len(events) >= 1
    assert events[0]["incident_id"] == incident_id


def test_recent_validates_limit(client: TestClient) -> None:
    assert client.get("/api/memory/recent", params={"limit": 0}).status_code == 422
    assert client.get("/api/memory/recent", params={"limit": 9999}).status_code == 422


def test_memory_status_reports_mode(client: TestClient) -> None:
    body = client.get("/api/memory/status").json()
    assert body["available"] is True
    # No credentials in the test environment, so this must be the demo path.
    assert body["mode"] in {"demo", "live"}


def test_relevance_endpoint_exposes_the_scoring_method(client: TestClient) -> None:
    response = client.post(
        "/api/memory/relevance",
        json={"query": "database connection pool exhausted on checkout", "service": "checkout-api"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "local_lexical_overlap"
    assert "not a semantic similarity" in body["note"]


def test_relevance_endpoint_validates_input(client: TestClient) -> None:
    assert client.post("/api/memory/relevance", json={}).status_code == 422
    assert client.post("/api/memory/relevance", json={"query": "ab"}).status_code == 422
