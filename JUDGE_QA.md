# IncidentMind — Judge Q&A

Answers are written to be defensible under questioning. Where the current
implementation is narrower than the design, that is stated — a judge who finds
out later is worse than one who is told up front.

---

### Why is this an agent?

Because the work is a decision procedure over evidence, not a lookup. For one
incident the system has to assemble current signals, decide what historical
experience is relevant, generate and rank competing failure hypotheses, pick a
remedy, attach a risk level, and stop for human approval. Each step depends on
the previous one, and the output of any step can change what the next step does.

A rule engine could do this if the failure modes were known in advance. They
are not — the whole point is incidents nobody has seen before. The reasoning is
delegated to a model, and the structure around it — evidence assembly,
constraint that it may only recommend, mandatory approval gate — is what makes
it an agent rather than a completion.

---

### Why is memory important?

Because incident response is a recall problem disguised as a diagnosis problem.

When an incident fires, the hardest part is not reading the current logs. It is
answering "have we seen this before, and what did we do about it?" In most teams
that answer is trapped in a postmortem doc from fourteen months ago, written by
someone who has since moved teams, in a format nobody will search at 3am.

Without memory, every incident restarts at zero and the organisation pays the
same diagnosis cost repeatedly. With memory, the second occurrence of a failure
class is genuinely cheaper than the first. That is the entire economic argument,
and it is why the demo is built around two incidents rather than one.

---

### Why Hindsight?

Because we needed memory that is **external to the model** and survives the
session. Fine-tuning cannot do this job — see the fine-tuning question below.

Hindsight gives us a durable store with retrieval built in, scoped to a bank id
so one organisation's operational experience does not leak into another's. We
write resolved experience into it, and we query it at the start of an
investigation. Because the memory is a separate service, the retrieval step is
observable, auditable, and replaceable — and a dead memory service degrades one
panel rather than the application.

---

### What is actually stored in memory?

Resolved experiences, not raw logs. For each retained incident we store:

- the incident identity and service
- the **root cause** that was concluded
- the **action** taken and its type
- the **outcome** — did it recover
- the **lesson** — what was learned
- supporting signal values

That is a compact, structured record of a decision and its result. Logs stay in
the log store; memory holds the conclusion. This keeps records small, keeps them
retrievable, and avoids putting sensitive payloads into a long-lived store.

---

### How does the system learn?

Through a **retain and recall loop**, not through weight updates.

1. An incident is investigated using current signals plus anything recalled.
2. A human approves an action. It is simulated and produces an outcome.
3. The incident is resolved and the experience is **retained** into memory.
4. On a later, similar incident, the recall step retrieves that experience
   before analysis begins.
5. The recalled experience enters the evidence set and informs the hypotheses
   and the recommendation.

The learning is in the **memory store and the retrieval**, not in the model. The
model is unchanged between incident A and incident B. What changed is the
evidence it was given.

---

### Is the model being fine-tuned?

No. Nothing in this system trains, tunes, or updates model weights.

Memory and fine-tuning solve different problems. Fine-tuning changes what a
model knows permanently and globally. We need the opposite: per-incident,
per-organisation, per-incident-shape context that is added at inference time and
can be inspected, corrected, or deleted on its own.

This is retrieval, not training. The practical consequences: a bad retained
memory is removable without retraining anything, and turning memory off
(`memory_enabled=False`) gives a clean control condition — same model, same
signals, no retrieval. That control is built into the API, not simulated.

---

### How do agents work together?

Two things, and it matters that they are different.

**Conceptually, the roles are:** Triage establishes severity and scope; Memory
recalls prior experience; Observability reads current signals and recent
changes. Those three findings converge into Root Cause, which compares
hypotheses; then Action Planner builds a candidate remedy; then Incident
Commander synthesises one recommendation for the operator.

**As actually implemented today, be precise:** the investigation is a
**sequential pipeline, not a set of concurrently running specialists**. In
`AgentService.investigate` the order is:

1. `MemoryService.recall(...)` — one recall call
2. `_analyse(...)` — **one** structured analysis call to the LLM provider
3. persistence of the run

The stage list you see rendered in the UI is generated by
`AgentService._investigation_steps`, which is an ordered, human-readable
narration of what actually happened. It is not a log of separate agent
processes. There is no `asyncio.gather`, no thread pool, and no per-specialist
model call in the current code.

So: the *reasoning* has specialist roles, and the UI presents them as such, but
they are not independently executing agents today. That is a deliberate,
correct call for a first version — each role needs the others' findings to be
worth running separately — but it is not what the animated network implies, and
you should not claim otherwise.

---

### Why parallel execution?

Because in a real system the first three roles do not need each other. Triage
reads incident metadata. Memory queries the memory store. Observability reads
telemetry. None of them depends on another's output, so serialising them pays
latency for nothing.

The answer that matters more than latency: **isolating the roles isolates their
failures and makes them independently auditable.** If the memory agent returns
nothing, the investigation should degrade and say so, not fail. If a future
specialist is slow, the others should not wait on it. Concurrency is what makes
that isolation real rather than aspirational.

Today that is a design intent, not an implementation. If asked directly, say so
— and note that the API already returns per-provider status and latency
(`ProviderStatus.latency_ms`), which is the observability you would need to
prove the split was real.

---

### What happens when memory has no match?

The investigation continues with current signals only. The memory panel says
**"No relevant historical experience found."**

This is a distinct, correct outcome — and it is reported differently from two
other cases, deliberately:

- memory **disabled** for the run → "Organisational memory was disabled"
- memory **searched and empty** → "No relevant historical experience found"
- memory **failed** → "Memory unavailable", provider status `degraded`

Those are three different facts. Collapsing them into one message would make a
broken integration look like a healthy system with nothing to report, which is
the failure mode this design is built to avoid. The `memory_enabled` flag also
travels into the prompt context so the model can tell the difference too.

---

### What happens if Hindsight fails?

It degrades; it does not propagate.

The provider layer is behind an interface with a factory that resolves to
`auto` — Hindsight when configured, the local SQLite mirror when it is not, and
the local path when a live call errors. The response carries a `ProviderStatus`
with `mode`, `available`, `detail` and `latency_ms`, and the UI surfaces the
degraded state.

A dead memory service costs you historical context on that investigation. It
does not cost you the investigation. The same principle holds for the LLM: if
every provider fails, the system returns a valid, explicitly-unavailable result
rather than a 500, and never fabricates a recommendation to fill the gap.

---

### Can it execute real production commands?

No, and there is no code path that could.

The action layer is `SimulatedActionProvider`, whose own health detail reads
`simulated action layer; no real execution path exists`. Approving an action
does not invoke a shell, an API, or a deploy tool — it produces deterministic
telemetry that converges toward a healthy baseline, labelled `SIMULATED` in the
interface.

Two further deliberate properties. Every investigation sets
`requires_human_approval=True` unconditionally, so an action cannot be
auto-approved. And the simulation is **outcome-sensitive**: approving the
recommended remedy recovers well, approving an unrelated one recovers poorly.
That makes the demo honest — the system is rewarded for being right, not for
being clicked.

Turning this into real execution would mean a new provider behind the same
interface plus a much harder approval story. It is a deployment decision, not
a code path waiting to be enabled.

---

### What makes this different from a chatbot?

A chatbot answers what you ask it. This investigates what happened.

The difference is who chooses the question. You do not prompt it — an incident
opens and the system decides what evidence to gather, what to recall, what to
hypothesise, and what to recommend. It produces an auditable investigation
record: ordered steps, ranked hypotheses with evidence, a recommendation with a
risk level, and a memory trail — not a paragraph.

The second difference is persistence. A chat session ends and is gone. Here the
output of a resolved incident is written to durable memory and changes the next
investigation. A chatbot forgets by default; this system accumulates by design.

---

### What makes this different from a normal incident dashboard?

A dashboard shows you what is happening. It does not tell you what to do, and it
certainly does not remember what you did last time.

Concretely, three things a standard dashboard cannot do:

- **It has no history of its own decisions.** Dashboards read live telemetry.
  Every time you open one, you start from zero. Here, the previous resolution is
  a retrievable input.
- **It cannot rank causes.** It shows a graph. This returns ranked hypotheses
  with the evidence behind each and a confidence value.
- **It has no completion.** It cannot propose a remedy, gate it for approval,
  and then record what was learned.

The demo exists to make the difference observable rather than asserted: the same
product, two incidents, and the second investigation is better informed because
of the first.

---

### How could this scale?

Horizontally, with three separate moves.

**Memory is already the scaling unit.** Retrieval is scoped by bank id, so
sharding memory per team, service, or environment is a routing decision rather
than a re-architecture. The bottleneck moves from "does the system remember" to
"how is relevant experience partitioned and ranked."

**Stateless orchestration.** The investigation is already a request-scoped
pipeline over a repository interface, so workers scale horizontally behind a
queue. The stateful part is deliberately small — the incident record and the
retained experience — which is the shape you want.

**Where it would actually get hard, stated honestly.** Three things. First,
*retrieval quality*: as memory grows, naive similarity returns plausible but
irrelevant experience, and ranking becomes the core problem — that is the real
work at scale, not storage. Second, *noisy memory*: retention needs quality
control, because a bad lesson recalled confidently is worse than no memory at
all. Third, *cost*: per-incident analysis is LLM spend, so triage prioritisation
and cheaper models for the early stages matter. The sequential pipeline is
actually an advantage here — it is a natural place to insert a small model for
triage and a large one only for synthesis.
