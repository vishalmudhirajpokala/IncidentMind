# IncidentMind — backend

A memory-first incident response agent. The loop it implements is:

> incident → signals → **recall how this organisation has seen this before** →
> recommendation → **human approval** → simulated action → resolution →
> **retain the experience** → the next similar incident starts from experience
> rather than from zero.

The memory is the product. Everything else exists to make one piece of retained
experience retrievable and usable on the next incident.

---

## Safety posture

**Nothing here executes anything.** There is no shell, no `kubectl`, no SSH, no
cloud SDK, and no code path that contacts a production system. The only action
surface is `SimulatedActionProvider`, which returns deterministic modelled
telemetry. Every action requires an explicit `"approved": true` (a strictly
typed boolean) or the API returns `409`.

Language is deliberate: IncidentMind *learns from experience through persistent
memory*. It does not fine-tune, and no performance improvement is claimed
anywhere in this codebase.

## Honesty rules enforced in code

| Rule | Where it is enforced |
|---|---|
| Hindsight returns no similarity score, so none is invented | `RetrievedMemory.score` stays `None`; relevance is computed locally and labelled `local_lexical_overlap` |
| Retain returns no created memory ids, so none are invented | `external_ids` is left empty for the external provider |
| A dead dependency degrades a response, it does not 500 | every provider wraps transport failures; `/api/health` is always `200` |
| Live vs demo is always labelled | `mode="live" | "demo" | "unavailable"` on every provider status |
| No fabricated metrics | `/api/metrics/overview` counts real rows; a test asserts no field looks like a benchmark percentage |
| No flattering zeros | `average_resolution_time_seconds` is computed only over incidents that actually recorded a duration, and is `null` — not `0` — when there are none. `incidents_with_measured_resolution` always travels with it so the sample size is visible |
| No secrets in memory | `_scrub()` runs over every retained field, including the structured metadata |
| No memory-off sabotage | memory OFF runs the same analyst on the same signals; the difference is only that history is withheld |

## Layers

```
app/api/            HTTP surface. No business logic.
app/services/       Orchestration and rules (agent, memory, incident, metrics).
app/repositories/   Data access. Returns SQLModel instances, not schemas.
app/models/         Persistence schema.
app/integrations/   Vendor adapters behind provider interfaces.
app/demo/           The deterministic learning-loop scenario.
app/prompts.py      Loads prompts/incident_investigation.txt and friends.
seed/               Reference corpus and the reset used by "Reset Demo".
tests/              pytest suite.
scripts/            Repeatable verification, not scratch files.
```

Provider-specific code stops at `app/integrations`. `app/integrations/factory.py`
is the only place that decides which vendor is in use.

## Providers

| Interface | Live | Demo / fallback |
|---|---|---|
| `MemoryProvider` | `HindsightMemoryProvider` | `LocalMemoryProvider` (SQLite mirror) |
| `LLMProvider` | `GroqLLMProvider` | `DeterministicLLMProvider` (rule-based analyst) |
| `ActionProvider` | — | `SimulatedActionProvider` (always simulated, by design) |

`DeterministicLLMProvider` is a genuine rule-based analyst: it classifies the
failure shape, applies the same weighted relevance function, and adapts the
remedy to the current release (for example rewriting a remembered rollback
against the live version). It is not canned text, and it reports
`mode="demo"` and low confidence when it has no evidence.

## Running it

```bash
pip install -r requirements.txt
copy .env.example .env       # optional: works with no credentials at all
uvicorn app.main:app --reload
```

- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/health>
- Demo scenario: `POST /api/demo/run`
- Restore the seeded state: `POST /api/demo/reset`

With no credentials the app still runs end to end in demo mode and labels every
response accordingly.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Per-dependency detail. Always `200`. |
| GET | `/api/incidents` | List, with `status` / `service` / `severity` filters |
| POST | `/api/incidents` | Create |
| GET | `/api/incidents/{id}` | Fetch one (`404` if unknown) |
| PATCH | `/api/incidents/{id}` | Update |
| DELETE | `/api/incidents/{id}` | Delete (`204`) |
| GET | `/api/incidents/{id}/history` | Investigation runs for an incident |
| POST | `/api/incidents/{id}/investigate` | The full loop. `memory_enabled: false` for the control path |
| POST | `/api/incidents/{id}/simulate-action` | Simulated, human-approved. `409` without approval |
| POST | `/api/incidents/{id}/resolve` | Resolve, and retain by default |
| POST | `/api/incidents/{id}/retain` | Retain the experience. `409` without a root cause |
| POST | `/api/memory/recall` | Multi-facet recall for an incident |
| POST | `/api/memory/relevance` | Transparent view of the scoring function |
| GET | `/api/memory/recent` | Recently retained experiences |
| GET | `/api/memory/status` | Which memory provider is actually serving |
| GET | `/api/metrics/overview` | Counts derived from real rows, plus `average_resolution_time_seconds` and `incidents_with_measured_resolution` |
| GET | `/api/demo/status` | Demo mode, and whether credentials are present |
| GET | `/api/demo/scenarios` | Description of the learning-loop scenario |
| POST | `/api/demo/run` | Runs the loop and reports the evidence |
| POST | `/api/demo/reset` | Restores the seeded state |
| GET | `/api/demo/history` | Investigation history across incidents |

## The demo scenario

`POST /api/demo/run` executes and reports the whole learning loop:

1. **Incident A** (checkout-api, pool exhausted after v2.9.0) is investigated
   with memory ON. It is the first such incident retained, so recall is empty
   and the recommendation is generic.
2. A human approves and the action is **simulated**.
3. A is resolved and its structured experience is **retained**.
4. **Incident B** arrives — same service, same failure pattern, a different
   release, and deliberately different wording (a customer complaint about
   hanging checkouts, never saying "pool", "exhausted" or "5xx").
5. B is investigated with memory **OFF** (control) and then memory **ON**.
6. The response names the historical incident, its root cause, its successful
   action, its outcome, and why it is relevant.

`learning_proven` is computed from the actual recall result. If the loop does
not close, the endpoint says so instead of claiming a success.

## Verification

Three layers, all repeatable:

```bash
python -m pytest tests -q              # 87 tests: contract, validation, failure modes
python scripts/verify_learning_loop.py # 33 checks: the full loop, in-process
python scripts/verify_http_server.py   # 35 checks: over a real uvicorn socket
```

Both verification scripts reset and re-seed data, so each one points
`DATABASE_URL` at a throwaway file before the app is imported. They will not
touch `incidents.db`. (The in-process one has to do this at module scope, before
the first `app` import, because settings and the engine are both built at import
time.)

The pytest suite covers the happy paths and, importantly, the degraded ones:
Hindsight pointed at a dead port, Groq unreachable, a memory provider that
raises on every call, malformed ids, wrong-typed bodies, secret scrubbing, and
the memory OFF vs ON comparison.

Helper scripts:

- `scripts/check_imports.py` — import smoke check and route table.
- `scripts/inspect_investigation.py` — prints one full investigation response,
  for reviewing what the agent actually tells a human.
- `scripts/reset_dev_db.py` — wipe and reseed the development database.

## Configuration

Every setting is typed in `app/config.py` and documented in `.env.example`.
Secrets come from the environment only; `.env` is git-ignored and only
`.env.example` is committed. `GET /api/demo/status` and `/api/health` report
*whether* a credential is present, never its value.

Set `APP_ENV=production` to disable automatic reference seeding.
