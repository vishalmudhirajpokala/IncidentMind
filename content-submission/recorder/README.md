# Demo recorder

A scripted screen recorder for the IncidentMind walkthrough. It drives the real
public deployment with a headless browser and writes a **1920×1080 WebM** of the
verified demo flow.

This is a submission asset, not product code. It imports nothing from
`frontend/` or `backend/` and does not touch the application.

```powershell
cd content-submission\recorder
npm install
npx playwright install chromium

npm run record                    # reset memory, record, clean up afterwards
npm run record -- --no-reset      # record against whatever memory holds now
npm run record -- --keep          # leave the created incident + memory in place
$env:HEADED = "1"; npm run record # watch it run in a real window
```

The video lands in `video/incidentmind-demo.webm`. Both `video/` and
`node_modules/` are git-ignored.

## What it does

1. Wakes the API and waits until `/api/health` reports `memory` and `database`
   both `live`. A free-tier cold start takes 30–50 seconds; it waits rather than
   filming a spinner.
2. Resets the Hindsight bank to exactly `INC-001`–`INC-004` and waits for it to
   index.
3. Records:
   - landing page, then dashboard
   - `INC-005` → **Investigate with memory** → the panel cites `INC-004`,
     `INC-001`, `INC-002`
   - **Retain experience to memory**
   - **Trigger a similar incident** → **Create and investigate**
   - the new incident → **Investigate with memory** → the panel cites `INC-005`,
     the experience retained seconds earlier
   - **Approve simulated action** → **Approve and simulate**
   - **Resolve and retain**
4. Deletes the incident it created and re-resets memory, so the app is left in
   the state `DEMO.md` describes.

## Why it resets memory first

The flow ends by retaining `INC-005`. Run it twice without a reset and the cold
open lands on an incident whose closest match is *itself* — the panel would cite
`INC-005`, which looks like a bug on camera. The reset makes every run produce
the same video.

## Why every wait is a condition, never a timer

The analysis is a live LLM behind a cold start. Fixed sleeps either cut the
result off or pad the video with dead air. The script waits for the recalled
incident ID to appear, which is self-correcting: it films the pause when the
model is slow and moves on when it is fast.

The one thing it cannot wait on is *wording*. The recommendation text varies
between runs even at temperature 0.1, so nothing keys off it.

## Honest limitations

- **The video is silent.** Playwright captures the page, not a microphone. Add
  narration afterwards, or talk over the playback.
- **Viewport only.** No browser chrome, no visible cursor movement between
  clicks, no typing of the URL. It reads as a screen recording of the app, not
  of a person using a computer.
- **It is not a substitute for the narration.** The pitch is the explanation of
  the loop; this produces the footage.
- **Every seeded incident ships resolved**, so the approve → resolve → retain
  arc is only available on an incident created during the session. That is why
  the flow creates one instead of resolving `INC-005` in place.
- The `--keep` flag exists so you can inspect the created incident afterwards.
  Without it, cleanup removes it, and the retained memory that pointed at it.
