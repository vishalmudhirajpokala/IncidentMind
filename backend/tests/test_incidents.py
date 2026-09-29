"""Incident CRUD, validation and error handling."""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_BODY = {
    "title": "Checkout latency regression after release",
    "service": "checkout-api",
    "severity": "high",
    "description": "p99 latency rose to 1.4s after the release shipped.",
    "signals": ["p99 latency 1400ms", "error rate 6%"],
    "metrics": {"error_rate": 6.0, "p99_latency_ms": 1400},
    "deployment_version": "v2.9.3",
    "recent_change": "deploy v2.9.3",
}


def test_list_returns_seeded_incidents(client: TestClient) -> None:
    response = client.get("/api/incidents")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 8
    ids = {i["id"] for i in body}
    assert {"INC-001", "INC-008"} <= ids


def test_list_respects_pagination(client: TestClient) -> None:
    response = client.get("/api/incidents", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_rejects_out_of_range_pagination(client: TestClient) -> None:
    assert client.get("/api/incidents", params={"limit": 0}).status_code == 422
    assert client.get("/api/incidents", params={"limit": 10_000}).status_code == 422
    assert client.get("/api/incidents", params={"skip": -1}).status_code == 422


def test_list_filters_by_service_and_severity(client: TestClient) -> None:
    response = client.get("/api/incidents", params={"service": "checkout-api"})
    assert response.status_code == 200
    assert response.json()
    assert all(i["service"] == "checkout-api" for i in response.json())

    response = client.get("/api/incidents", params={"severity": "critical"})
    assert response.status_code == 200
    assert all(i["severity"] == "critical" for i in response.json())


def test_get_existing_incident(client: TestClient) -> None:
    response = client.get("/api/incidents/INC-001")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "INC-001"
    assert body["service"] == "checkout-api"
    assert body["root_cause"]


def test_get_unknown_incident_returns_404(client: TestClient) -> None:
    response = client.get("/api/incidents/INC-NOPE")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_handles_malformed_id(client: TestClient) -> None:
    """A path that is not a valid id is a 404, not a 500."""
    for bad in ("!!!", "../../etc/passwd", "1;DROP TABLE incident", "%00", "a" * 400):
        response = client.get(f"/api/incidents/{bad}")
        assert response.status_code in {404, 405}, f"{bad!r} produced {response.status_code}"


def test_create_incident(client: TestClient) -> None:
    response = client.post("/api/incidents", json=VALID_BODY)
    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("INC-")
    assert body["title"] == VALID_BODY["title"]
    assert body["signals"] == VALID_BODY["signals"]
    assert body["metrics"]["error_rate"] == 6.0

    # It is immediately retrievable, proving it reached the database.
    assert client.get(f"/api/incidents/{body['id']}").status_code == 200


def test_create_assigns_unique_ids(client: TestClient) -> None:
    first = client.post("/api/incidents", json=VALID_BODY).json()["id"]
    second = client.post("/api/incidents", json=VALID_BODY).json()["id"]
    assert first != second


def test_create_rejects_missing_required_fields(client: TestClient) -> None:
    for body in (
        {},
        {"title": "no service"},
        {"service": "no title"},
        {"title": "x", "service": "y"},  # title too short
    ):
        assert client.post("/api/incidents", json=body).status_code == 422, body


def test_create_rejects_invalid_enum_values(client: TestClient) -> None:
    assert (
        client.post("/api/incidents", json={**VALID_BODY, "severity": "catastrophic"}).status_code
        == 422
    )
    assert (
        client.post("/api/incidents", json={**VALID_BODY, "status": "on-fire"}).status_code
        == 422
    )


def test_create_rejects_wrongly_typed_fields(client: TestClient) -> None:
    assert client.post("/api/incidents", json={**VALID_BODY, "signals": "not a list"}).status_code == 422
    assert client.post("/api/incidents", json={**VALID_BODY, "metrics": "not a dict"}).status_code == 422


def test_update_incident(client: TestClient) -> None:
    response = client.patch("/api/incidents/INC-001", json={"status": "resolved", "lesson": "New lesson"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["lesson"] == "New lesson"
    # Untouched fields are preserved.
    assert body["service"] == "checkout-api"


def test_update_unknown_incident_returns_404(client: TestClient) -> None:
    assert client.patch("/api/incidents/NOPE", json={"status": "resolved"}).status_code == 404


def test_delete_incident(client: TestClient) -> None:
    response = client.delete("/api/incidents/INC-001")
    assert response.status_code == 204
    assert client.get("/api/incidents/INC-001").status_code == 404


def test_delete_unknown_incident_returns_404(client: TestClient) -> None:
    assert client.delete("/api/incidents/INC-NOPE").status_code == 404
