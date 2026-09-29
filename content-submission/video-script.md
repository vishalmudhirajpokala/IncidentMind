# Three-Minute Demo Script

**Recording setup:** Open the frontend at `http://localhost:3000/dashboard`. Use a disposable local database or a clean development copy: **Run learning loop** creates incidents and investigation records in the active database. Do not reset a database that contains work you need. Keep the provider-mode badge visible; the verified script run used the local memory mirror and deterministic analyst.

## 0:00–0:25 — Intro

**Show:** Dashboard header, provider-mode badges, incident list.

**Say:** “Hi, I’m [YOUR NAME]. I built IncidentMind, an incident-response command center that connects current signals to prior incident experience. The goal is simple: when an incident repeats, the next investigation should be able to show what the team learned last time.”

## 0:25–0:55 — The problem

**Show:** Open an incident and point to its service, deployment, signals, and memory state. Then show the memory-off control path or the side-by-side run comparison.

**Say:** “A model can reason about this incident, but without organizational memory it starts with only the current symptoms. I keep the memory-off run as a control: same incident, same signals, same analyst, with historical evidence withheld. An empty result and an unavailable provider are different states too.”

## 0:55–2:30 — Retain, recall, and compare

**Show:** Click **Run learning loop** on the dashboard. Open the incident pair created by the loop. Compare the memory-off and memory-on investigation results. Point at the recalled incident ID, its root cause, prior action, outcome, and `why_relevant` explanation. Show the recommendation version change.

**Say:** “The learning loop starts with a checkout failure after a release. IncidentMind records the investigation, requires human approval for the simulated action, resolves the incident, and retains structured experience. A second checkout incident describes the same failure pattern differently. The memory-off path recommends a generic rollback. The memory-on path can cite the earlier incident and recommend the last known-good version.”

“Here the evidence says which incident was recalled, what action worked, what happened afterward, and why the record matched. The relevance label is local lexical overlap in this verified run; it is not a similarity score returned by Hindsight.”

**Show:** Briefly switch to `backend/app/services/memory_service.py` and `backend/app/integrations/hindsight_provider.py`. Point to the multi-facet query and the provider’s recall/retain calls. Keep the `/api/health` provider mode visible.

**Say:** “The memory service builds a query from service, symptoms, signals, metrics, deployment, and failure pattern. Hindsight is the external provider boundary. This repository’s repeatable verification uses the local provider, so I’m not presenting that run as a live Hindsight request. When a live bank is configured and verified, the provider label should say so.”

## 2:30–3:00 — Takeaway

**Show:** Return to the incident recommendation and retained learning entry.

**Say:** “The important part is not that the agent produced a confident answer. It is that the recommendation can point to a retained experience, and the operator still approves any action. My main takeaway: make memory provenance visible, keep the control path fair, and never let a recommendation silently become permission to act.”

## Five Video Title Options

- An Incident Agent That Can Show What It Remembered
- How Hindsight Memory Changes an Incident Recommendation
- From One Checkout Failure to the Next Investigation
- I Built an Incident Response Loop That Keeps Its Lessons
- Why Incident Memory Needs a Real Control Path
