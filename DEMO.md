# IncidentMind — Demo Guide

Two demo paths are documented. **Path A is the real thing.** Use Path B only if
an external service is down mid-pitch.

Everything below is verified against the running application. Where a number is
quoted it comes from a real API response, not an estimate.

---

## Before you start

Everything below is verified against the **public deployment**. You can also run
it locally, and both are covered here.

### Option 1 — the public deployment (nothing to start)

Open <https://incidentmind-eight.vercel.app>.

Warm it first: load
<https://incidentmind-eight.vercel.app/backend/api/health> once and wait for
`"memory":"live"`. The free hosting tier sleeps after 15 minutes idle, so the
first request after a pause takes **30–50 seconds**. That is a cold start, not a
fault — do not click anything until the status line settles.

A cold start re-seeds the incident list from the reference corpus
(`INC-001`–`INC-008`). The Hindsight memories live outside that database and are
never lost. See "The ephemeral database" below.

**State the demo expects.** Hindsight holds retained experience for
`INC-001`–`INC-004`. Those are the "previous incidents" recalled in step 3.
`INC-005` is deliberately **not** retained, so its panel cites other incidents
instead of itself; step 5 retains it live. If someone has investigated or
retained `INC-005` already in your session, its panel will cite `INC-005`, which
looks like a circle — pick a different non-retained incident (`INC-006`,
`INC-007`, `INC-008`) for step 3, or note it and move on.

### Option 2 — run it locally

Both services must be running. The frontend alone is not enough — every panel
reads from the API.

```powershell
# Terminal 1 — API (port 8010)
cd C:\Users\VISHAL\OneDrive\Desktop\HWH-3.0\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010

# Terminal 2 — web app (port 3000)
cd C:\Users\VISHAL\OneDrive\Desktop\HWH-3.0\frontend
npm run dev
```

Then open <http://localhost:3000>. The incident corpus is the same, so every
incident number below works identically on both routes.

**Check this before you walk in.** The landing page hero carries a live status
line that should read:

```
API connected · operational mode
```

That is the expected reading on the public deployment — Groq and Hindsight are
both live, so `demo_mode` is `false`. If it reads `API connected · demo mode`,
check `/backend/api/health`: one of the two providers has stopped answering.
The demo still works, but see "The honest limitation" below before you narrate
it. If it reads `Waiting for the IncidentMind API`, the API is not up — stop and
fix that first.

---

## Path A — The 60–90 second demo

Target time: **75 seconds**, leaving room for questions.

### 1 · Landing page (10s)

Open the deployment — <https://incidentmind-eight.vercel.app> (or
<http://localhost:3000> if you are running locally).

Land on the hero. One sentence, out loud:

> "IncidentMind is an AI incident response console. The thing that makes it
> different is that it remembers — every resolution becomes context for the
> next incident."

Scroll to the **Hindsight memory** section. Point at the loop:
`Incident → Investigate → Resolve → Retain → Hindsight → Recall`.

> "This loop is the product. I'll show you the second half of it working."

Click **Open Command Center**.

### 2 · Dashboard — orient (10s)

Four KPI cards are live: Active incidents, Resolved incidents, Avg resolution
time, Experiences in memory.

Point at **Experiences in memory** and say the number out loud. It is the
backlog of retained experience.

> "These are real query results, not placeholders."

Do **not** walk the incident table. That is a list, not a story.

### 3 · Incident A — investigate with memory (25s)

Open **`/incidents/INC-005`** (*Timeout errors after caching layer change*).

Read the header aloud: service, severity, status, detection time.

Scroll to the **current signals** — error rate, latency, DB connections, the
recent deployment. This is the "today" half of the input.

Now click **Investigate**.

Wait for it to finish — a few seconds with both providers live. Then point at
four things, in this order:

1. **Investigation timeline** — the ordered list of what the system actually did.
2. **Hindsight memory** — the recalled prior incidents, each with *why it is
   relevant*. The verified recall for INC-005 is **`INC-004`**, **`INC-001`**
   and **`INC-002`** — three real incidents from the reference corpus. The
   panel's own headline names `INC-004` as the strongest match. Say: "These are
   from previous incidents that already happened."
3. **Recommendation** — the action, the risk level, and the evidence.
4. **Confidence** — and note it is higher here *because* memory contributed.

The single most important sentence of the whole demo:

> "It didn't just read the logs. It read what we learned the last time this
> happened."

### 4 · Approve, act, resolve (15s)

Click **Approve and simulate**.

The action runs and is labelled **SIMULATED** in the UI. Say it out loud, and
explain why in one line:

> "Nothing executes against real infrastructure. It produces simulated
> telemetry so you can see the outcome without the risk."

Watch the error-rate figure move. Then click **Resolve**.

### 5 · Retain (10s)

Click **Retain experience**.

Confirmation: `Experience added to organisational memory`.

This is the hinge of the demo. Pause on it.

> "That experience is now in memory. It is not a postmortem document nobody
> reads — it is retrievable input for the next investigation."

### 6 · Incident B — the payoff (20s)

On INC-005's page, click **Trigger a similar incident**, then **Create**.

This creates a **new** incident on the same service, worded deliberately
*differently* from INC-005 — the dialog says so on screen, and it is the point:
retrieval has to match on the failure shape rather than on shared keywords.

When it opens, click **Investigate**. Scroll straight to **Hindsight memory**.

> "Same product, different incident. The experience we just retained is in this
> list."

Stop talking. Let them read the recalled experience. This is the moment the
whole pitch rests on. The verified recall here is **`INC-005`** — the incident
you retained one step ago — and the recommendation rolls the version back to
the one that experience recorded.

> Do **not** claim the wording is meaningless. The new incident's text is a
> fixed demonstration phrasing, not telemetry. The dialog labels it
> *Simulated input*; leave that badge visible and say the word "simulated".

### 7 · Close (5s)

> "That is the loop. A resolved incident changed how the next one was handled."

---

## The one thing to emphasise

At step 6, make the causal link explicit. A judge should be able to draw this:

```
Incident A  →  resolved  →  experience retained  →  memory
                                                        ↓
Incident B  →  investigated  ←──────────────  experience recalled
```

If they only remember one thing, make it this. Not the UI, not the agents, not
the font — **the second investigation was different because of the first.**

---

## Path B — Backup demo

Use this only if a real external service is failing. Every screen still works;
only the provider behind it changes.

### If the LLM is unavailable

The investigation still completes. The summary degrades to:

> "Automated analysis is unavailable, so no recommendation can be made."

That is intentional, not a crash — the system reports the failure instead of
inventing an answer. Say so. *"It refuses to hallucinate a recommendation. I
prefer that to a confident wrong answer."*

### If Hindsight is unavailable

The memory panel shows **"Memory unavailable"** and the investigation continues
with current signals only. The dashboard status line reports the degraded
provider. Point out that the rest of the product is unaffected — a dead
dependency degrades one panel, not the app.

### If the whole API is down

You cannot run the demo. The landing page still renders (it is static) and every
other section still tells the product story — the narrative does not depend on
the API. Walk the landing page and explain the loop. Do not pretend the console
works.

### If the API is up but memory is empty

The memory panel says **"No relevant historical experience found."** This is a
correct response, not a failure — it means nothing has been retained yet for
this failure shape. Run the loop once to populate it: open **`INC-005`**,
investigate, resolve, retain, then trigger the similar incident.

---

## The ephemeral database — know this before you present

The free hosting tier has **no persistent disk**. The API's SQLite database is
rebuilt from the reference corpus every time the service wakes from sleep, so
the incident list always returns to `INC-001`–`INC-008`.

Three consequences:

1. **Incidents you create during a session will disappear** on the next sleep.
   That includes anything from *Trigger a similar incident*. Do the whole loop
   in one sitting, or accept starting over.
2. **Retained experience survives.** Hindsight is an external service. Memories
   written in an earlier session are still there when the database resets —
   which is exactly the property the product is about, and it is genuinely true
   here rather than asserted.
3. **A retained memory can outlive the incident it came from.** If you retain a
   dynamically created incident and the database later resets, that memory
   refers to an incident ID that no longer exists. Prefer retaining
   `INC-001`–`INC-005`, which are always re-seeded.

The rehearsed path avoids the trap entirely: everything it touches is in the
reference corpus, and the only dynamically created incident is investigated
inside the same session.

---

## Rehearsal checklist

- [ ] Public URL warmed — load `/backend/api/health` and confirm `"memory":"live"`
- [ ] Browser at <https://incidentmind-eight.vercel.app> (or <http://localhost:3000>), zoom 100%
- [ ] Full path rehearsed end to end at least twice
- [ ] Timed — under 90 seconds
- [ ] You can say what is stored in memory without notes
- [ ] You can say why actions are simulated without notes
- [ ] You know the one honest nuance: Hindsight chooses which past incidents
      come back, but it returns no similarity score, so the *"Relevant
      because…"* sentence is computed locally and labelled
      `local_lexical_overlap`. Point at the incident IDs; do not attribute the
      explanation line to Hindsight. See below.

---

## The honest limitation — say it if asked

Both providers are live on the public deployment, and `/api/health` says so:

- `llm: mode=live` — `openai/gpt-oss-20b` over Groq
- `memory: mode=live` — Hindsight, bank `incidentmind-demo`

If a key is removed or a provider stops answering, the same endpoint flips to
`mode=demo` and the app degrades instead of failing: recall falls back to a
lexical match over the local SQLite mirror, and analysis falls back to a
deterministic rule-based analyst. Both are labelled `demo` in the UI. The
architecture is identical either way — the provider interface swaps, the loop
does not.

**The one thing not to overclaim.** Hindsight performs the retrieval — it
decides which past incidents are relevant. It does not return a similarity
score, so the app computes its own explanation sentence locally and labels it
`local_lexical_overlap` rather than dressing it up as a Hindsight score.

If a judge presses on that, the honest answer is: *"Hindsight picks the
evidence. The sentence under it is ours, and it says so in the metadata. I'd
rather label it than pass it off as a score the provider never returned."*

Claiming live Hindsight when `/api/health` says `mode=demo` is the one thing
that would make the whole demo untrustworthy. The label exists precisely so you
can be caught being honest.
