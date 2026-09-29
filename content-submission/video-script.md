# IncidentMind — Video Script (YouTube)

Recording-ready. Every claim below matches what the application actually does
right now. Do not record a line that the running app would contradict.

**Runtime state this script assumes:**

| | status |
|---|---|
| LLM | `groq` / **live** — `openai/gpt-oss-20b` |
| Memory | `hindsight` configured but **402 Payment Required**; recall degrades to the local SQLite mirror |
| Backend | port 8010 |
| Frontend | port 3000 |

That memory state matters for how you narrate. See "The one line to get right"
at the bottom.

---

## Recording setup

**Before you press record:**

```powershell
# Terminal 1
cd C:\Users\VISHAL\OneDrive\Desktop\HWH-3.0\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010

# Terminal 2
cd C:\Users\VISHAL\OneDrive\Desktop\HWH-3.0\frontend
npm run dev
```

**Capture tool — nothing to install.** Windows built-ins:

- **Win + Alt + R** — starts/stops screen recording. Simplest option.
- **Win + Shift + S** → select the **video** mode — snip a region, more control
  over framing.

Alternatively OBS Studio, if you want to overlay a webcam in the corner.

**Settings that matter**

- Record at **1920x1080**. The layout is verified at 1440 and 1920; below 1024
  the tables reflow and look cramped on video.
- Close Slack, Discord, email. A notification banner mid-demo ruins a take.
- Zoom the browser to **100%**. Anything else and the type looks wrong.
- Use a **dark or light theme consistently** — don't switch mid-video, the
  palette is tuned for both but the switch is jarring on camera.

**Groq rate limit.** Rapid-fire investigations return `429 Too Many Requests`
and *silently* fall back to the deterministic analyst. Pause a few seconds
between takes. If an investigation returns in under a second, you got rate
limited — retake it.

---

## 0:00–0:15 — Cold open

**Show:** Incident page for `/incidents/INC-011`, scrolled to the Hindsight
memory panel, cursor resting on a recalled incident.

**Say:**

> "This panel shows three incidents from the past that had this same failure
> shape. This system is called IncidentMind, and the reason it exists is to make
> sure that when an incident repeats, the next investigation doesn't start from
> zero."

No logo animation. Open on the product.

---

## 0:15–0:40 — The problem

**Show:** Scroll up to the current signals. Point at error rate, latency, DB
connections, and the deployment version.

**Say:**

> "Here's the 'today' half of the input. Current telemetry, and a release that
> went out shortly before the error rate climbed."

**Show:** Cut to `/dashboard`, four KPI cards.

> "A normal dashboard shows you this and stops. It has no memory of what you did
> the last time this happened, and it can't tell you what to do next."

---

## 0:40–1:20 — Investigate

**Show:** Click **Investigate**. Wait for it to land — **2 to 5 seconds with the
live model.** Do not rush this; the pause is evidence that a real model is
thinking.

**Say:**

> "Three things just happened. It parsed the signals, it recalled prior
> experience, and it generated ranked hypotheses."

**Show:** Point at the recommendation card.

> "Read the *why*: it names the specific past incident, and says the same remedy
> worked before. That's the difference — it isn't proposing a generic rollback,
> it's citing evidence."

**Optional but strong:** point at the confidence value, then say:

> "Confidence is higher than the same investigation would get without the
> recalled evidence, because the recommendation is backed by precedent rather
> than inference alone."

---

## 1:20–2:00 — Approve, resolve, retain

**Show:** Click **Approve and simulate**. Watch the error rate move. Then
**Resolve**, then **Retain experience**.

**Say:**

> "Nothing executed against real infrastructure. This is simulated telemetry so
> you can see the outcome without the risk, and a human approved it. I'm now
> retaining the experience — root cause, action, outcome, and the lesson."

Let the confirmation sit on screen for a beat. This is the hinge of the video.

---

## 2:00–2:45 — The payoff

**Show:** Trigger a similar incident (or open `/incidents/INC-016`), click
**Investigate**, scroll straight to the memory panel.

**Say:**

> "Same product. Different incident. And the experience we just retained is in
> this list."

**Stop talking here.** Let them read it. Then, slowly:

> "The first incident was resolved. Its experience was retained. It came back
> when a similar incident arrived. That is the whole product."

---

## 2:45–3:00 — Close

**Say:**

> "IncidentMind. Every resolved incident makes the next response smarter. The
> model isn't retrained — the learning lives in the memory store, which is why
> you can inspect it, correct it, or delete it. Thanks for watching."

---

## The one line to get right

Your memory provider is **not live right now** — Hindsight returns
`402 Payment Required`, so recall degrades to a local lexical mirror.

If a viewer asks "is that real Hindsight?", the honest answer is:

> "The architecture is identical either way — it's a provider interface. Right
> now the Hindsight account has no credit, so recall is served from the local
> mirror and the app labels it `degraded` rather than pretending. The health
> endpoint and the UI both show that. I wanted the failure visible instead of
> hidden."

**Do not say** "Hindsight recalled these" on this recording. Say "the system
recalled these." The distinction is small on video and enormous if a judge
checks.

Conversely, the LLM **is** live, and you can say so plainly. If you get Hindsight
credit before recording, re-check `/api/health` — if `memory.mode` reads `live`,
then and only then name Hindsight on camera.

---

## Title and description

**Title options**

- I Built an Incident Agent That Remembers What Went Wrong Before
- The 3-Second Moment That Proves an AI Actually Learned
- From One Checkout Failure to the Next: An Incident Memory Loop
- Why Every Incident Dashboard Forgets (and What I Built Instead)

**Thumbnail:** the memory panel with three recalled incident IDs, one
highlighted, plus the phrase "it remembered."

**Description opener:**

> IncidentMind is an AI incident response console where every resolved incident
> becomes retrievable context for the next investigation. Built with FastAPI,
> Next.js, Groq (live LLM) and a Hindsight memory provider boundary.

---

## Shot list (for editing)

| # | Time | Source | Note |
|---|---|---|---|
| 1 | 0:00 | `/incidents/INC-011` memory panel | Cold open, no title card |
| 2 | 0:15 | same, scroll up to signals | |
| 3 | 0:30 | `/dashboard` | KPI cards |
| 4 | 0:45 | back to INC-011, click Investigate | **Leave the 2–5s wait in** |
| 5 | 1:00 | recommendation card | The "why" is the money shot |
| 6 | 1:20 | Approve → Resolve → Retain | Confirmation must be legible |
| 7 | 2:00 | `/incidents/INC-016` Investigate → memory | **The payoff. Don't cut early.** |
| 8 | 2:45 | dashboard or incident, wide | Close |

Capture 4, 5 and 7 in **separate takes** and assemble. You cannot rewind a
5-second model response if you flub the narration over it.
