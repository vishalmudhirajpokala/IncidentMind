"""System routes: health, root, OpenAPI."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["app"] == "IncidentMind"


def test_health_reports_each_dependency(client: TestClient) -> None:
    body = client.get("/api/health").json()
    for key in ("database", "memory", "llm"):
        assert key in body, f"health is missing dependency detail for {key}"
        assert "available" in body[key]
        assert "mode" in body[key]
        assert "latency_ms" not in body[key] or body[key]["latency_ms"] is None


def test_health_never_leaks_credentials(client: TestClient) -> None:
    raw = client.get("/api/health").text
    assert "GROQ_API_KEY" not in raw
    assert "HINDSIGHT_API_KEY" not in raw


def test_root_lists_endpoints(client: TestClient) -> None:
    body = client.get("/").json()
    assert body["service"] == "IncidentMind"
    assert "endpoints" in body
    assert "never executes" in body["safety"].lower()


def test_openapi_document_is_valid(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()

    required = [
        "/api/health",
        "/api/incidents",
        "/api/incidents/{incident_id}",
        "/api/incidents/{incident_id}/investigate",
        "/api/incidents/{incident_id}/simulate-action",
        "/api/incidents/{incident_id}/resolve",
        "/api/incidents/{incident_id}/retain",
        "/api/memory/recall",
        "/api/memory/recent",
        "/api/metrics/overview",
        "/api/demo/scenarios",
        "/api/demo/reset",
    ]
    for path in required:
        assert path in spec["paths"], f"{path} is missing from the OpenAPI document"


def test_request_id_is_correlated(client: TestClient) -> None:
    response = client.get("/api/health")
    assert "X-Request-ID" in response.headers

    supplied = client.get("/api/health", headers={"X-Request-ID": "abc123"})
    assert supplied.headers["X-Request-ID"] == "abc123"
