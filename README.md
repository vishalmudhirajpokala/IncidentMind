# IncidentMind

A memory-first AI incident response agent.

When an incident is declared, IncidentMind recalls how this organisation has
seen the failure before, recommends a reversible action grounded in that
history, hands the decision to a human, and then retains the outcome so the
next incident on the same service starts from experience instead of from
scratch.

The claim is narrow and checkable: **memory changes the recommendation, and
you can see exactly what it contributed.** The UI shows the recalled
experiences, the confidence with and without them, and the experience written
back at the end.

```
backend/    FastAPI service, memory + LLM adapters, SQLite, 26 routes
frontend/   Next.js public landing page and operational console
```

## Quick start

Two processes. The backend first.

```bash
# 1. backend  (http://127.0.0.1:8000)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000

# 2. frontend (http://localhost:3000)
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000/> for the public landing page, then choose **Open
Command Center** to enter the existing dashboard at `/dashboard`.

No credentials are required. With none configured the app runs in **demo mode**:
a local memory mirror and a deterministic analyst, with every result labelled
demo rather than live. See [Integrations](#integrations-status) for what changes
when you add keys.

If port 8000 is taken on your machine, point the frontend elsewhere without
editing a tracked file:

```bash
# frontend/.env.local
API_INTERNAL_URL=http://127.0.0.1:8010
```

## Routes

| Route | What it is for |
| --- | --- |
| `/` | Public product landing page and entry to the command center |
| `/dashboard` | Command center: KPIs with sample sizes, the incident table, recent learning, and what memory measurably changed |
| `/incidents/[id]` | The investigation workspace: signals, recalled memory, recommendation, human approval, simulated outcome, resolution and retention |
| `/history` | Every investigation run, for after-the-fact comparison |

There is deliberately no separate memory dashboard. Memory is shown where it is
used, because a memory browser that nobody consults during an incident is not
part of an incident response system.

## The 90-second demo

1. On `/dashboard`, press **Run learning loop**. Two incidents on the same
   service, worded differently. The second is analysed twice — once with memory
   withheld, once with it — and the report shows the recommendation changing and
   the confidence gap.
2. Open the second incident.
3. **Compare without memory** puts the two runs side by side: the generic
   remedy versus the cited one, and the confidence delta.
4. **Approve simulated action** — requires naming an approver. Returns
   before/after telemetry. Nothing touches real infrastructure.
5. **Resolve and retain** — pre-filled from the agent's own output, editable.
6. **Trigger a similar incident** — a new incident on the same service described
   in deliberately different words. Investigating it recalls the experience
   retained seconds earlier, and the new recommendation cites it.

Step 6 is the one that matters. The new incident shares no vocabulary with the
first, so retrieval has to match on failure shape rather than keywords.

## Design commitments

These are enforced in code, not just intended:

- **Nothing executes without human approval.** There is no auto-approve path in
  the UI, and the request sends the JSON literal `approved: true` rather than
  coercing a loose value into consent.
- **Withheld ≠ empty ≠ unavailable.** "Memory was withheld for the control run"
  is not the same claim as "memory has nothing relevant", and neither is "the
  memory service is down". Each has its own wording, in both the API and the UI.
- **LIVE vs DEMO is never implicit.** The header always shows the memory and
  model mode, sourced from `/api/health`.
- **Relevance scores are attributed.** Hindsight's recall API returns no
  similarity score, so the one shown is computed locally and labelled
  `local overlap`. A locally computed number is never presented as if the
  provider produced it.
- **No fabricated numbers.** Every figure counts real rows. Where a mean has an
  empty sample the API returns `null` rather than `0`, and the UI shows the
  sample size. "What memory changed" states that it is an observation of these
  runs, not a benchmark.
- **No chain-of-thought.** Only a short user-safe reasoning summary.
- **No credentials in the browser.** Hindsight and Groq keys live only in the
  backend environment. The frontend proxies to the backend from the server side
  and never learns its address.
- **No blank screens.** Every failure renders a named state with the next move.
  Error messages carry no stack traces and no credentials.

## Verification

Backend, three layers, all repeatable:

```bash
cd backend
python -m pytest tests -q               # 87 tests
python scripts/verify_learning_loop.py  # 33 checks: the full loop, in-process
python scripts/verify_http_server.py    # 35 checks: over a real uvicorn socket
```

Both scripts point `DATABASE_URL` at a throwaway file first, so verifying never
touches your working data.

Frontend:

```bash
cd frontend
npm run typecheck   # tsc --noEmit, strict
npm run build       # production build
```

Accessibility and touch-target regressions are caught by Lighthouse on all
three screens in both light and dark themes, against the production build, in
each screen's richest state (accessibility, best-practices and SEO all score
1.0). The palette's lightnesses are solved for the surface a badge actually sits
on by `frontend/scripts/mono_contrast.py` rather than chosen by eye, and the
layout is checked for overflow and column alignment at eight widths from 360px to
1920px.

## Interface

The public landing page introduces the incident-response workflow, specialist
agent roles, and Hindsight memory. The operational console retains its dashboard,
incident-investigation, and history routes.

**Palette.** The interface uses the verified blue ramp `#0A369D`, `#4472CA`,
`#5E7CE2`, `#92B4F4`, and `#CFDDFE` with light and dark neutral surfaces. Status
labels remain textual; colour is supplementary.

**Typography.** DM Sans is loaded with `next/font` and applied globally. Roboto
Mono is reserved for technical identifiers and telemetry.

`frontend/README.md` covers the block provenance, the reused-versus-discarded
list, the deviations, and how the palette and font wiring are solved.

## Integrations status

Be precise about this, because it is the part that is easy to overstate.

| Capability | State |
| --- | --- |
| Memory recall / retain via `LocalMemoryProvider` | Working, exercised by the test suite and both gates |
| Analysis via `DeterministicLLMProvider` | Working, same |
| Live Hindsight (`HINDSIGHT_BASE_URL` + key) | **Unverified.** The adapter is written from the published API reference. No live server has been contacted. |
| Live Groq (`GROQ_API_KEY`) | **Unverified.** Same. |

Both live adapters are written to the documented request and response shapes and
degrade cleanly when the dependency is absent, but until they are pointed at a
real endpoint and exercised, the correct description is "written against the
API reference", not "working". Everything currently demonstrated runs on the
local mirror and the deterministic analyst, and the UI says so on every screen.

The retrieval query always carries `SERVICE:`, `SYMPTOMS:`, `SIGNALS:`,
`CHANGE:`, `CONTEXT:` and `FAILURE PATTERN:` facets, so recall matches on
failure shape rather than keyword overlap.

## Known limits

- SQLite only, no migrations. Fine for a demo, not for a service.
- `LocalMemoryProvider` is a lexical matcher: two incidents sharing no
  vocabulary will not match. The demo's third step is worded specifically to
  prove the facet matching works, not the general case.
- Nothing is fine-tuned, and nothing claims to be. Learning here means a
  structured record is written to memory and retrieved later, which is a
  different and much smaller claim.
- Only the memory-on and memory-off runs for the same incident are directly
  comparable. The aggregate "what memory changed" figure mixes incidents and is
  labelled as an observation, not a benchmark.

## More detail

- `backend/README.md` — API surface, provider resolution, runbook
- `frontend/README.md` — architecture, design rules, demo flow, and what was
  reused from the shadcn/ui `dashboard-01` block versus discarded, including the
  one place the block's content was not reproducible and why
