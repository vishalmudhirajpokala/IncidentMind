"""Repeatable end-to-end verification of the learning loop.

Runs the full gate against the real app, exercising HTTP the same way a client
would, and prints one PASS/FAIL line per check.

    python scripts/verify_learning_loop.py
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# This script resets and re-seeds the database, so it must never touch the
# developer's working data. `app.config` reads the environment at import time
# and `app.database` builds the engine then too, so the override has to happen
# before the first `app` import - not inside main().
_SCRATCH = tempfile.mkdtemp(prefix="incidentmind-verify-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_SCRATCH, 'verify.db')}"


@atexit.register
def _cleanup() -> None:
    shutil.rmtree(_SCRATCH, ignore_errors=True)


from fastapi.testclient import TestClient  # noqa: E402

from app.database import create_all, session_scope  # noqa: E402
from app.main import app  # noqa: E402
from seed.seed_incidents import reset_and_seed  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    RESULTS.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def main() -> int:
    create_all()
    with session_scope() as session:
        reset_and_seed(session)

    client = TestClient(app)

    # ---------------------------------------------------------------- health
    r = client.get("/api/health")
    body = r.json()
    check("GET /api/health returns 200", r.status_code == 200, f"status={r.status_code}")
    check(
        "health reports all three dependencies",
        all(k in body for k in ("database", "memory", "llm")),
        f"status={body.get('status')}, memory={body.get('memory', {}).get('mode')}, "
        f"llm={body.get('llm', {}).get('mode')}",
    )

    # -------------------------------------------------------------- incidents
    r = client.get("/api/incidents")
    seeded = r.json()
    check("GET /api/incidents returns seeded data", r.status_code == 200 and len(seeded) >= 8, f"count={len(seeded)}")

    r = client.get("/api/incidents/INC-001")
    check("GET /api/incidents/INC-001 returns 200", r.status_code == 200)

    r = client.get("/api/incidents/DOES-NOT-EXIST")
    check("GET unknown incident returns 404", r.status_code == 404, f"status={r.status_code}")

    r = client.post("/api/incidents", json={"title": "x"})
    check("POST /api/incidents rejects an invalid body with 422", r.status_code == 422, f"status={r.status_code}")

    r = client.post(
        "/api/incidents",
        json={
            "title": "Validation probe incident",
            "service": "probe-service",
            "severity": "critical",
            "description": "Created by the verification script.",
        },
    )
    check("POST /api/incidents creates with 201", r.status_code == 201, f"status={r.status_code}")
    probe_id = r.json()["id"] if r.status_code == 201 else None

    r = client.post("/api/incidents/does-not-exist/investigate", json={})
    check("investigate unknown incident returns 404", r.status_code == 404, f"status={r.status_code}")

    # -------------------------------------------------------- approval guard
    if probe_id:
        r = client.post(
            f"/api/incidents/{probe_id}/simulate-action",
            json={"action": "Restart the service"},
        )
        check(
            "unapproved action is rejected with 409",
            r.status_code == 409,
            f"status={r.status_code}",
        )

        r = client.post(
            f"/api/incidents/{probe_id}/retain",
        )
        check(
            "retain without a root cause is rejected with 409",
            r.status_code == 409,
            f"status={r.status_code}",
        )

        r = client.post(
            f"/api/incidents/{probe_id}/simulate-action",
            json={"action": "x"},
        )
        check(
            "simulate-action rejects a too-short action with 422",
            r.status_code == 422,
            f"status={r.status_code}",
        )

    # ------------------------------------------------------------ demo reset
    r = client.post("/api/demo/reset")
    check("POST /api/demo/reset returns 200", r.status_code == 200, json.dumps(r.json().get("cleared", {})))

    r = client.get("/api/demo/scenarios")
    check("GET /api/demo/scenarios returns 200", r.status_code == 200)

    # --------------------------------------------------- the learning loop
    r = client.post("/api/demo/run")
    check("POST /api/demo/run returns 200", r.status_code == 200)
    if r.status_code != 200:
        print(json.dumps(r.json(), indent=2)[:3000])
        return 1

    demo = r.json()
    steps = {s["step"]: s for s in demo["steps"]}

    check(
        "incident A investigated with memory ON",
        steps[1]["memory_count"] == 0,
        f"A recalled {steps[1]['memory_count']} memories, action='{steps[1]['recommended_action']}'",
    )
    check(
        "human approved action was simulated and succeeded",
        steps[2]["success"] is True and steps[2]["simulated"] is True,
        steps[2]["message"],
    )
    check(
        "incident A resolved and retained to memory",
        steps[3]["retained"] is True,
        f"retain_status={steps[3]['retain_status']}, event={steps[3]['memory_event_id']}",
    )
    check(
        "memory OFF run for incident B found no history",
        steps[4]["memory_count"] == 0 and steps[4]["mode"] == "memory_off",
        f"action='{steps[4]['recommended_action']}' confidence={steps[4]['confidence']}",
    )
    check(
        "memory ON run for incident B recalled experience",
        steps[5]["memory_count"] >= 1,
        f"source={steps[5]['memory_source']}, action='{steps[5]['recommended_action']}' "
        f"confidence={steps[5]['confidence']}",
    )

    ev = steps[6]
    check(
        "incident B recalled incident A specifically",
        ev["retrieved"] is True,
        f"historical_incident_id={ev['historical_incident_id']}",
    )
    check(
        "evidence includes A's root cause, action and outcome",
        bool(ev["historical_root_cause"]) and bool(ev["historical_action"]) and bool(ev["historical_outcome"]),
        f"relevance={ev['relevance']} ({ev['relevance_method']})",
    )
    check(
        "evidence includes a relevance rationale",
        bool(ev["why_relevant"]),
        ev["why_relevant"],
    )
    check("demo reports the learning loop as proven", demo["learning_proven"] is True, demo["summary"])

    # memory OFF must not be handicapped
    off_action = steps[4]["recommended_action"]
    on_action = steps[5]["recommended_action"]
    check(
        "memory ON produced a more specific recommendation than memory OFF",
        on_action != off_action,
        f"OFF='{off_action}'\n        ON ='{on_action}'",
    )
    check(
        "memory ON confidence exceeds memory OFF confidence",
        steps[5]["confidence"] > steps[4]["confidence"],
        f"OFF={steps[4]['confidence']} ON={steps[5]['confidence']}",
    )

    # ------------------------------------------------------------- endpoints
    a_id = steps[1]["incident_id"]
    b_id = steps[5]["incident_id"]

    r = client.post("/api/memory/recall", json={"incident_id": b_id})
    recall = r.json()
    check(
        "POST /api/memory/recall returns the recalled experience",
        r.status_code == 200 and recall["count"] >= 1,
        f"source={recall.get('source')}, count={recall.get('count')}",
    )

    r = client.post("/api/memory/recall", json={"incident_id": "NOPE-1"})
    check("POST /api/memory/recall on an unknown id returns 404", r.status_code == 404, f"status={r.status_code}")

    r = client.get("/api/memory/recent", params={"limit": 5})
    check("GET /api/memory/recent returns 200", r.status_code == 200, f"count={len(r.json())}")

    r = client.get("/api/metrics/overview")
    metrics = r.json()
    check("GET /api/metrics/overview returns 200", r.status_code == 200)
    check(
        "metrics counts both memory ON and OFF investigations",
        metrics["investigations_memory_on"] >= 1 and metrics["investigations_memory_off"] >= 1,
        f"on={metrics['investigations_memory_on']} off={metrics['investigations_memory_off']} "
        f"memories={metrics['memory_events_total']} external={metrics['memory_events_external']}",
    )

    r = client.get(f"/api/incidents/{b_id}/history")
    check("GET /api/incidents/{id}/history returns 200", r.status_code == 200, f"runs={len(r.json()['investigations'])}")

    r = client.get("/api/demo/status")
    check("GET /api/demo/status returns 200", r.status_code == 200)

    # ------------------------------------------------------- a final re-check
    r = client.post("/api/demo/run")
    check(
        "the loop is repeatable on a second run",
        r.status_code == 200 and r.json()["learning_proven"] is True,
        f"learning_proven={r.json().get('learning_proven')}" if r.status_code == 200 else f"status={r.status_code}",
    )

    passed = sum(1 for _n, ok, _d in RESULTS if ok)
    total = len(RESULTS)
    print("\n" + "=" * 70)
    print(f"{passed}/{total} checks passed")
    print("=" * 70)
    if passed != total:
        print("\nFailures:")
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  - {name}: {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
