# IncidentMind — Video Script (YouTube)

Recording-ready. Every claim below matches what the application actually does
right now. Do not record a line that the running app would contradict.

**Runtime state this script assumes:**

| | status |
|---|---|
| LLM | `groq` / **live** — `openai/gpt-oss-20b` |
| Memory | `hindsight` / **live** — bank `incidentmind-demo`, reads and writes confirmed |
| Public URL | `https://incidentmind-eight.vercel.app` (live, proxied to the deployed API) |

Both providers are live, so you can name Groq **and** Hindsight on camera.
Re-check `/backend/api/health` immediately before you record — if `memory.mode`
ever reads anything but `live`, drop the Hindsight name. See "The one line to
get right" at the bottom.

**Anchor incident: `INC-005`** (*Timeout errors after caching layer change*). It
is in the reference corpus, so it exists on the public URL and locally. The
verified recall for it is **`INC-004`, `INC-001` and `INC-002`** — three real
incidents, all resolvable. Do not use an incident number outside
`INC-001`–`INC-008`; anything higher existed only in a local scratch database.

**Memory is pre-loaded with `INC-001`–`INC-004`.** Those are the "previous
incidents" the cold open recalls from. `INC-005` is deliberately *not* retained,
so its panel cites other incidents rather than itself. You retain it live during
the take, at the 1:20 mark.

---

## Recording setup

**Recommended: record against the public URL.** Nothing to start, and the
video shows judges exactly what they will see when they click the link.

1. Open `https://incidentmind-eight.vercel.app/backend/api/health` in a tab.
2. Confirm it reads `"memory":"live"` and `"llm":"live"`.
3. That request also **wakes the API** — the free tier sleeps after 15 minutes
   idle and the first real request after a pause takes 30–50s. Do this
   immediately before you press record, not during it.
4. Open the console in a second tab and record that one.

**Fallback: record locally** if the network misbehaves on the day.

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

**Show:** Incident page for `/incidents/INC-005`, scrolled to the Hindsight
memory panel, cursor resting on a recalled incident.

**Say:**

> "This panel shows three incidents from the past that had this same failure
> shape — `INC-004`, `INC-001`, `INC-002`. This system is called IncidentMind,
> and the reason it exists is to make sure that when an incident repeats, the
> next investigation doesn't start from zero."

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

**Show:** Point at the recommendation card — first the action, then the two
counters underneath it (*Evidence*, *History*).

> "Two real numbers behind this recommendation. *Evidence*: it drew on three
> prior experiences. *History*: this remedy already succeeded before on this
> service. That's the difference — not a generic rollback, but a remedy it has
> seen work."

Do **not** say this card names a past incident — it doesn't. It counts evidence
and states whether the remedy has precedent. The incident IDs are one panel
over, in **Hindsight memory**.

**Show:** Point at **Hindsight memory**, then at the confidence value.

> "Confidence is the agent's own figure for this run. What makes it worth
> trusting is the panel beside it — the evidence is inspectable rather than
> hidden inside the model."

> Do **not** claim confidence is *higher* because memory contributed. That
> comparison was never measured. State the number, and point at the evidence.

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

**Show:** On INC-005's page, click **Trigger a similar incident** → **Create**.
A new incident opens. Click **Investigate**, then scroll straight to the memory
panel.

> Leave the **Simulated input** badge visible — the dialog labels the new
> incident's text as a canned phrasing, and it is. Don't call it telemetry.

**Say:**

> "Same product, different incident — and the wording is deliberately different,
> so this isn't matching on keywords. The experience we retained thirty seconds
> ago is in this list, by name: `INC-005`."

**Stop talking here.** Let them read the recalled entry. Then, slowly:

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

Both providers are live, so you can name Groq and Hindsight plainly. But there
is one nuance worth understanding, because it is the only part of the memory
panel that a sharp judge could challenge.

**Hindsight performs the retrieval. The sentence explaining the retrieval does
not come from Hindsight.**

Hindsight returns no similarity score, so the app falls back to its own
documented lexical matcher to produce the *"Relevant because it is shared
symptoms (…)"* line — and labels it `local_lexical_overlap` rather than
attributing it to Hindsight. This is deliberate, and the comment in
`app/services/memory_service.py` says so.

What that means on camera:

- **Do** say Hindsight chose which past incidents to surface. That is true.
- **Do not** narrate the "Relevant because…" text as if Hindsight wrote it.
- If asked, the honest answer is:

> "Hindsight does the semantic retrieval — it decides which past incidents are
> relevant. It doesn't return a similarity score, so the app computes its own
> explanation locally and labels it as such rather than dressing it up as a
> Hindsight score. The evidence list is Hindsight's; the sentence under it is
> ours."

**On camera, point at the incident IDs, not the explanation line.** The IDs are
the proof. The explanation line is the weakest thing on the screen and you
don't have to draw attention to it.

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
| 1 | 0:00 | `/incidents/INC-005` memory panel | Cold open, no title card |
| 2 | 0:15 | same, scroll up to signals | |
| 3 | 0:30 | `/dashboard` | KPI cards |
| 4 | 0:45 | back to INC-005, click Investigate | **Leave the 2–5s wait in** |
| 5 | 1:00 | recommendation card + memory panel | Point at *Evidence*/*History*, then the IDs |
| 6 | 1:20 | Approve → Resolve → Retain | Confirmation must be legible |
| 7 | 2:00 | Trigger similar → Investigate → memory | **The payoff. Don't cut early.** |
| 8 | 2:45 | dashboard or incident, wide | Close |

Capture 4, 5 and 7 in **separate takes** and assemble. You cannot rewind a
5-second model response if you flub the narration over it.

**One more time, because it is the easiest thing to get wrong:** the memory
panel names past incidents. The recommendation card counts them. Don't swap
those two claims.
