"""Demo mode, metrics, and the memory ON/OFF comparison."""

from __future__ import annotations

from fastapi.testclient import TestClient


# ------------------------------------------------------------------ metrics
def test_metrics_overview_counts_real_rows(client: TestClient) -> None:
    response = client.get("/api/metrics/overview")
    assert response.status_code == 200
    body = response.json()

    assert body["incidents_total"] >= 8
    assert body["incidents_resolved"] >= 8
    assert body["investigations_total"] == 0
    assert body["by_service"].get("checkout-api") == 2
    assert body["providers"]["memory"]["available"] is True
    assert "average_confidence_memory_on" in body


def test_metrics_reflect_activity(client: TestClient) -> None:
    incident_id = client.post(
        "/api/incidents",
        json={"title": "Metric probe", "service": "probe", "description": "x"},
    ).json()["id"]

    client.post(f"/api/incidents/{incident_id}/investigate", json={})
    client.post(f"/api/incidents/{incident_id}/investigate", json={"memory_enabled": False})
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={"root_cause": "cause", "action_taken": "action", "outcome": "ok", "lesson": "l"},
    )

    body = client.get("/api/metrics/overview").json()
    assert body["investigations_total"] == 2
    assert body["investigations_memory_on"] == 1
    assert body["investigations_memory_off"] == 1
    assert body["memory_events_total"] == 1
    assert body["average_confidence_memory_on"] is not None


def test_metrics_contains_no_fabricated_percentages(client: TestClient) -> None:
    """No field may look like a benchmark improvement figure."""
    body = client.get("/api/metrics/overview").json()
    for key in body:
        assert "percent" not in key.lower()
        assert "improvement" not in key.lower()
        assert "faster" not in key.lower()
        assert "%" not in key


# --------------------------------------------------------------------- demo
def test_demo_status_labels_the_active_providers(client: TestClient) -> None:
    body = client.get("/api/demo/status").json()
    assert "demo_mode" in body
    assert "memory_configured" in body
    assert "llm_configured" in body
    # Never echo a credential, only whether one is present.
    assert "not-a-real-key" not in str(body)


def test_demo_scenarios_describes_the_loop(client: TestClient) -> None:
    response = client.get("/api/demo/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert body["incident_a"]["service"] == body["incident_b"]["service"] == "checkout-api"
    assert body["incident_a"]["deployment_version"] != body["incident_b"]["deployment_version"]
    assert len(body["expected"]) >= 5
    # The two incidents must be worded differently but operationally the same.
    assert body["incident_a"]["title"] != body["incident_b"]["title"]


def test_demo_reset_restores_the_seeded_state(client: TestClient) -> None:
    incident_id = client.post(
        "/api/incidents",
        json={"title": "Throwaway", "service": "throwaway", "description": "x"},
    ).json()["id"]
    client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={"root_cause": "c", "action_taken": "a", "outcome": "o", "lesson": "l"},
    )
    assert client.get("/api/memory/recent").json()

    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    cleared = response.json()["cleared"]
    assert cleared["memories"] >= 1
    assert cleared["seeded"] == 8

    assert client.get("/api/memory/recent").json() == []
    assert client.get(f"/api/incidents/{incident_id}").status_code == 404
    assert len(client.get("/api/incidents").json()) == 8


def test_demo_run_proves_the_learning_loop(client: TestClient) -> None:
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    body = response.json()
    steps = {s["step"]: s for s in body["steps"]}

    # 1. A starts with no history of its own.
    assert steps[1]["memory_count"] == 0

    # 2. The human approves and the action is simulated, never executed.
    assert steps[2]["simulated"] is True
    assert steps[2]["success"] is True

    # 3. A is resolved and retained.
    assert steps[3]["retained"] is True
    assert steps[3]["memory_event_id"]

    # 4. The control path sees nothing.
    assert steps[4]["memory_count"] == 0
    assert steps[4]["mode"] == "memory_off"

    # 5. The memory path sees the retained experience.
    assert steps[5]["memory_count"] >= 1
    assert steps[5]["mode"] == "memory_on"
    assert steps[5]["confidence"] > steps[4]["confidence"]

    # 6. The evidence is complete and attributable.
    evidence = steps[6]
    assert evidence["historical_incident_id"] == steps[1]["incident_id"]
    assert evidence["historical_root_cause"]
    assert evidence["historical_action"]
    assert evidence["historical_outcome"]
    assert evidence["why_relevant"]
    assert evidence["relevance"] > 0

    assert body["learning_proven"] is True
    assert steps[1]["incident_id"] in body["summary"]


def test_demo_run_is_repeatable_after_a_reset(client: TestClient) -> None:
    """The same sequence must produce the same conclusion every time."""
    recommendations = []
    confidences = []

    for _ in range(2):
        assert client.post("/api/demo/reset").status_code == 200
        run = client.post("/api/demo/run").json()
        assert run["learning_proven"] is True

        steps = {s["step"]: s for s in run["steps"]}
        recommendations.append(steps[5]["recommended_action"])
        confidences.append(steps[5]["confidence"])

    # Deterministic fixtures: the same input yields the same recommendation.
    assert recommendations[0] == recommendations[1]
    assert confidences[0] == confidences[1]


# ------------------------------------------------- memory OFF vs memory ON
def test_memory_off_is_not_sabotaged(client: TestClient) -> None:
    """The control must still produce a usable, honest recommendation."""
    incident_id = client.post(
        "/api/incidents",
        json={
            "title": "Pool exhaustion after release",
            "service": "checkout-api",
            "description": "Database connection pool exhausted after deploying v2.8.1.",
            "signals": ["error rate 18%"],
            "metrics": {"error_rate": 18.0},
            "deployment_version": "v2.8.1",
        },
    ).json()["id"]

    off = client.post(
        f"/api/incidents/{incident_id}/investigate", json={"memory_enabled": False}
    ).json()

    assert off["memory_count"] == 0
    # It still reasons about the current evidence and recommends something real.
    assert off["hypotheses"]
    assert off["recommended_action"] is not None
    assert off["recommended_action"]["risk"] in {"low", "medium", "high"}
    assert off["recommended_action"]["simulated"] is True
    assert off["recommended_action"]["requires_approval"] is True
    # It is honest about *why* it has no history: withheld, not absent.
    limitations = off["limitations"].lower()
    assert "withheld" in limitations
    assert "no relevant historical experience exists" not in limitations


def test_memory_off_and_on_differ_only_in_what_memory_adds(client: TestClient) -> None:
    payload = {
        "title": "Pool exhaustion after release",
        "service": "checkout-api",
        "description": "Database connection pool exhausted after deploying v2.8.1.",
        "signals": ["error rate 18%"],
        "metrics": {"error_rate": 18.0},
        "deployment_version": "v2.8.1",
    }
    seed_id = client.post("/api/incidents", json=payload).json()["id"]
    client.post(
        f"/api/incidents/{seed_id}/resolve",
        json={
            "root_cause": "Connection leak in v2.8.1.",
            "action_taken": "Rolled back checkout-api from v2.8.1 to v2.8.0",
            "outcome": "Error rate fell to 1.4%.",
            "lesson": "Roll back on pool saturation after a release.",
        },
    )

    off = client.post(
        f"/api/incidents/{seed_id}/investigate", json={"memory_enabled": False}
    ).json()
    on = client.post(f"/api/incidents/{seed_id}/investigate", json={}).json()

    # Same incident, same analyst, same signals.
    assert off["incident"]["id"] == on["incident"]["id"]
    assert off["llm_provider"]["name"] == on["llm_provider"]["name"]

    # Memory adds the history, the citation and the higher confidence.
    assert off["memory_count"] == 0
    assert on["memory_count"] >= 1
    assert on["memory_evidence"][0]["source_incident_id"] == seed_id
    assert on["confidence"] > off["confidence"]
    assert seed_id in on["recommended_action"]["action"]


def test_demo_history_lists_runs(client: TestClient) -> None:
    client.post("/api/demo/run")
    body = client.get("/api/demo/history").json()
    assert body["investigations"]
    modes = {i["mode"] for i in body["investigations"]}
    assert {"memory_on", "memory_off"} <= modes
