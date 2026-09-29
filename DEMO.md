# IncidentMind — Demo Guide

Two demo paths are documented. **Path A is the real thing.** Use Path B only if
an external service is down mid-pitch.

Everything below is verified against the running application. Where a number is
quoted it comes from a real API response, not an estimate.

---

## Before you start

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

Then open <http://localhost:3000>.

**Check this before you walk in.** The top of the dashboard and the command
center both show a live status line. It should read
`API connected · demo mode` or `API connected · operational mode`. If it reads
`Waiting for the IncidentMind API`, the backend is not up and the demo will not
work. Stop and fix that first.

> `demo mode` is not a lesser product — it is the honest label for which
> providers answered. See "Backup demo" below.

---

## Path A — The 60–90 second demo

Target time: **75 seconds**, leaving room for questions.

### 1 · Landing page (10s)

Open <http://localhost:3000>.

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

Open **`/incidents/INC-011`**.

Read the header aloud: service, severity, status, detection time.

Scroll to the **current signals** — error rate, latency, DB connections, the
recent deployment. This is the "today" half of the input.

Now click **Investigate**.

Wait for it to finish. Then point at four things, in this order:

1. **Investigation timeline** — the ordered list of what the system actually did.
2. **Hindsight memory** — the recalled prior incidents, each with *why it is
   relevant*. Say: "These are from previous incidents that already happened."
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

Click **Trigger a similar incident** (or navigate to **`/incidents/INC-016`**).

This is a different incident with a similar failure shape. Click **Investigate**.

Scroll straight to **Hindsight memory**.

> "Same product, different incident. The experience we just retained is in this
> list."

Stop talking. Let them read the recalled experience. This is the moment the
whole pitch rests on.

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
correct response, not a failure. Run the loop once to populate it: investigate
INC-011, resolve, retain, then trigger the similar incident.

---

## Rehearsal checklist

- [ ] Both terminals running; status line reads `API connected`
- [ ] Browser at <http://localhost:3000>, logged out of nothing, theme as you like
- [ ] Full path rehearsed end to end at least twice
- [ ] Timed — under 90 seconds
- [ ] You can say what is stored in memory without notes
- [ ] You can say why actions are simulated without notes
- [ ] You know the one honest limitation: without API keys, memory is a local
      lexical match and the analyst is deterministic — both correctly labelled
      as demo. The architecture is identical either way; the providers swap.

---

## The honest limitation — say it if asked

Without a Hindsight key, `GET /api/health` reports `memory: mode=demo`. Without
a Groq key it reports `llm: mode=demo`.

In that state, recall is a **lexical** match over the SQLite mirror and analysis
comes from a deterministic rule-based analyst. The retention→recall loop is
genuinely real and observable, but it is not semantic search and it is not a
language model.

Say it plainly if a judge presses. Claiming live Hindsight when the health
endpoint says `mode=demo` is the one thing that would make the whole demo
untrustworthy. The label exists precisely so you can be caught being honest.
