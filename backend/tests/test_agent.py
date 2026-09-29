"""The agent loop: investigate, approve, simulate, resolve, retain."""

from __future__ import annotations

from fastapi.testclient import TestClient

NEW_INCIDENT = {
    "title": "Checkout requests timing out on the datastore",
    "service": "checkout-api",
    "severity": "high",
    "description": "Requests are timing out waiting on a database connection. Error rate 19%.",
    "signals": ["error rate 19%", "connection waits rising"],
    "metrics": {"error_rate": 19.0, "p99_latency_ms": 4100},
    "deployment_version": "v2.9.0",
}


def _new_incident(client: TestClient) -> str:
    response = client.post("/api/incidents", json=NEW_INCIDENT)
    assert response.status_code == 201
    return response.json()["id"]


# ------------------------------------------------------------------ investigate
def test_investigate_returns_200_with_full_shape(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(f"/api/incidents/{incident_id}/investigate", json={})
    assert response.status_code == 200
    body = response.json()

    for key in (
        "mode",
        "summary",
        "reasoning_summary",
        "hypotheses",
        "recommended_action",
        "confidence",
        "memory_enabled",
        "memory_count",
        "memory_evidence",
        "memory_source",
        "memory_status",
        "llm_provider",
        "requires_human_approval",
        "request_id",
    ):
        assert key in body, f"investigation result is missing {key}"

    assert body["mode"] == "memory_on"
    assert body["requires_human_approval"] is True
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["summary"]


def test_investigate_accepts_an_empty_body(client: TestClient) -> None:
    incident_id = _new_incident(client)
    assert client.post(f"/api/incidents/{incident_id}/investigate").status_code == 200


def test_investigate_unknown_incident_returns_404(client: TestClient) -> None:
    assert client.post("/api/incidents/NOPE/investigate", json={}).status_code == 404


def test_investigate_rejects_non_boolean_memory_flag(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(
        f"/api/incidents/{incident_id}/investigate", json={"memory_enabled": "yes please"}
    )
    assert response.status_code == 422


def test_investigate_memory_off_uses_no_memory(client: TestClient) -> None:
    """The control path must genuinely withhold memory, and say so."""
    incident_id = _new_incident(client)
    body = client.post(
        f"/api/incidents/{incident_id}/investigate", json={"memory_enabled": False}
    ).json()

    assert body["mode"] == "memory_off"
    assert body["memory_enabled"] is False
    assert body["memory_count"] == 0
    assert body["memory_evidence"] == []
    assert body["memory_query"] is None
    assert "memory" in (body["memory_detail"] or "").lower()
    # The analyst must distinguish "memory was withheld" from "memory is empty".
    # Claiming no relevant experience exists would misrepresent the control run.
    limitations = body["limitations"].lower()
    assert "memory" in limitations
    assert "withheld" in limitations
    assert "no relevant historical experience exists" not in limitations


def test_investigate_memory_flag_via_query_param(client: TestClient) -> None:
    incident_id = _new_incident(client)
    body = client.post(
        f"/api/incidents/{incident_id}/investigate", params={"memory_enabled": "false"}
    ).json()
    assert body["mode"] == "memory_off"


def test_memory_on_produces_cited_evidence(client: TestClient) -> None:
    """After a retain, a new investigation must surface the stored experience
    with full provenance, not just a count."""
    first = _new_incident(client)
    client.post(
        f"/api/incidents/{first}/resolve",
        json={
            "root_cause": "Connections were never returned to the pool.",
            "action_taken": "Rolled back checkout-api from v2.9.0 to v2.8.4",
            "outcome": "Error rate fell to 0.8%.",
            "lesson": "Saturated pool after a release means leaked connections.",
        },
    )

    second = _new_incident(client)
    body = client.post(f"/api/incidents/{second}/investigate", json={}).json()

    assert body["memory_count"] >= 1
    evidence = body["memory_evidence"][0]
    for key in (
        "source_incident_id",
        "historical_root_cause",
        "historical_action",
        "historical_outcome",
        "why_relevant",
        "relevance",
        "relevance_method",
    ):
        assert key in evidence, f"evidence is missing {key}"

    assert evidence["source_incident_id"] == first
    assert "never returned" in evidence["historical_root_cause"]
    assert "v2.8.4" in evidence["historical_action"]
    assert evidence["why_relevant"]

    # The recommendation must be grounded in the recalled incident.
    assert first in body["recommended_action"]["action"]


def test_investigation_is_persisted_for_history(client: TestClient) -> None:
    incident_id = _new_incident(client)
    client.post(f"/api/incidents/{incident_id}/investigate", json={})
    body = client.get(f"/api/incidents/{incident_id}/history").json()
    assert body["incident_id"] == incident_id
    assert len(body["investigations"]) == 1
    assert body["investigations"][0]["mode"] == "memory_on"


# --------------------------------------------------------------------- actions
def test_unapproved_action_is_refused(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(
        f"/api/incidents/{incident_id}/simulate-action",
        json={"action": "Rollback checkout-api to v2.8.4"},
    )
    assert response.status_code == 409
    assert "approval" in response.json()["detail"].lower()


def test_approved_action_is_simulated(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(
        f"/api/incidents/{incident_id}/simulate-action",
        json={
            "action": "Rollback checkout-api to v2.8.4",
            "approved": True,
            "approved_by": "oncall@example.com",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["simulated"] is True
    assert "no production system" in body["notes"].lower()
    assert body["action_type"] == "rollback"
    assert body["telemetry"]
    assert body["telemetry"][0]["metric"] == "error_rate"
    assert body["telemetry"][0]["before"] > body["telemetry"][0]["after"]


def test_simulated_action_is_deterministic(client: TestClient) -> None:
    incident_id = _new_incident(client)
    payload = {"action": "Rollback checkout-api to v2.8.4", "approved": True}
    first = client.post(f"/api/incidents/{incident_id}/simulate-action", json=payload).json()
    second = client.post(f"/api/incidents/{incident_id}/simulate-action", json=payload).json()
    assert first["telemetry"] == second["telemetry"]
    assert first["message"] == second["message"]


def test_action_body_validation(client: TestClient) -> None:
    incident_id = _new_incident(client)
    assert (
        client.post(f"/api/incidents/{incident_id}/simulate-action", json={}).status_code == 422
    )
    assert (
        client.post(
            f"/api/incidents/{incident_id}/simulate-action", json={"action": "x", "approved": True}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/incidents/{incident_id}/simulate-action",
            json={"action": "do a thing", "approved": "yes"},
        ).status_code
        == 422
    )


def test_simulate_action_unknown_incident_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/incidents/NOPE/simulate-action", json={"action": "Restart", "approved": True}
    )
    assert response.status_code == 404


# --------------------------------------------------------------------- resolve
def test_resolve_marks_resolved_and_retains(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Connection leak introduced by the release.",
            "action_taken": "Rolled back checkout-api from v2.9.0 to v2.8.4",
            "outcome": "Error rate returned to baseline.",
            "lesson": "Roll back first when the pool saturates after a release.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["retained"] is True
    assert body["memory_event_id"]

    incident = client.get(f"/api/incidents/{incident_id}").json()
    assert incident["status"] == "resolved"
    assert incident["resolved_at"] is not None
    assert incident["root_cause"] == "Connection leak introduced by the release."


def test_resolve_can_skip_retention(client: TestClient) -> None:
    incident_id = _new_incident(client)
    body = client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={"root_cause": "x", "outcome": "resolved", "retain": False},
    ).json()
    assert body["retained"] is False
    assert body["memory_event_id"] is None


def test_resolve_validates_body(client: TestClient) -> None:
    incident_id = _new_incident(client)
    assert (
        client.post(
            f"/api/incidents/{incident_id}/resolve",
            json={"outcome": "resolved", "resolution_time_seconds": -5},
        ).status_code
        == 422
    )


def test_resolve_survives_a_failed_retain(client: TestClient) -> None:
    """Resolving without a root cause still resolves.

    Retention is a follow-up effect, not part of resolving the incident, so a
    failed retain must not turn a completed resolution into an error.
    """
    incident_id = _new_incident(client)
    response = client.post(f"/api/incidents/{incident_id}/resolve", json={"outcome": "resolved"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["retained"] is False
    assert body["retain_status"] == "failed"

    # The resolution itself is durable.
    assert client.get(f"/api/incidents/{incident_id}").json()["status"] == "resolved"


def test_resolve_unknown_incident_returns_404(client: TestClient) -> None:
    assert client.post("/api/incidents/NOPE/resolve", json={"outcome": "x"}).status_code == 404


# ---------------------------------------------------------------------- retain
def test_retain_requires_a_root_cause(client: TestClient) -> None:
    incident_id = _new_incident(client)
    response = client.post(f"/api/incidents/{incident_id}/retain")
    assert response.status_code == 409
    assert "root cause" in response.json()["detail"].lower()


def test_retain_stores_a_structured_experience(client: TestClient) -> None:
    incident_id = _new_incident(client)
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Connection leak in the release.",
            "action_taken": "Rolled back to v2.8.4",
            "failed_action": "Restarting the pods did not help.",
            "outcome": "Recovered in 4 minutes.",
            "lesson": "Roll back on pool saturation after a release.",
        },
        # resolve already retained; retain again explicitly to inspect the shape
    )

    response = client.post(f"/api/incidents/{incident_id}/retain")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] in {"retained", "retained_locally"}
    # Offline test run: the local mirror, not an external service.
    assert body["external_retained"] is False
    assert body["provider"] == "local"


def test_retained_experience_has_all_required_fields(client: TestClient) -> None:
    incident_id = _new_incident(client)
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Connection leak in the release.",
            "action_taken": "Rolled back to v2.8.4",
            "failed_action": "Restarting the pods did not help.",
            "outcome": "Recovered in 4 minutes.",
            "lesson": "Roll back on pool saturation after a release.",
        },
    )

    events = client.get("/api/memory/recent", params={"incident_id": incident_id}).json()
    assert events
    event = events[0]
    metadata = event["event_metadata"]

    for key in (
        "incident_id",
        "service",
        "symptoms",
        "signals",
        "metrics",
        "deployment",
        "investigation",
        "root_cause",
        "actions_tried",
        "successful_action",
        "failed_action",
        "outcome",
        "resolution_time",
        "lesson",
    ):
        assert key in metadata, f"retained experience is missing {key}"

    assert "Stack trace" not in (event["content"] or "")
    assert metadata["failed_action"] == "Restarting the pods did not help."


def test_retain_scrubs_secrets(client: TestClient) -> None:
    incident_id = _new_incident(client)
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={
            "root_cause": "Misconfigured DSN postgres://user:hunter2@db:5432/app",
            "action_taken": "Corrected the connection string",
            "outcome": "Recovered",
            "lesson": "Check the DSN after config changes",
        },
    )
    event = client.get("/api/memory/recent", params={"incident_id": incident_id}).json()[0]
    blob = (event["content"] or "") + str(event["event_metadata"])
    assert "hunter2" not in blob
    assert "[redacted]" in blob


def test_retain_unknown_incident_returns_404(client: TestClient) -> None:
    assert client.post("/api/incidents/NOPE/retain").status_code == 404
