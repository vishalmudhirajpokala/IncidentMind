# IncidentMind — Frontend

Next.js (App Router) + Tailwind v4, built on the official shadcn/ui
**`dashboard-01` block**, talking to the FastAPI backend in `../backend`.

Public landing page and operational console:

| Route | Purpose |
| --- | --- |
| `/` | Public product landing page; the primary CTA opens the command center |
| `/dashboard` | Command center: KPIs, incident table, recent learning, memory effect |
| `/incidents/[id]` | Investigation workspace: signals, memory, recommendation, approval, outcome, retention |
| `/history` | Every investigation run recorded, for after-the-fact comparison |
| `/robots.txt` | Allows the public landing page; disallows console and backend proxy routes |

There is deliberately **no** separate memory dashboard. Memory is surfaced where
it is used: inside the investigation, and as "Recent learning" on the command
center.

## What came from the `dashboard-01` block

The block was installed with `shadcn add dashboard-01` and then rewritten in
place. The point of using it was to keep shadcn's own layout, spacing and
component system rather than re-deriving one, so what survived is worth naming.

**Reused, unmodified in intent:**

- `components/ui/*` — 16 `radix-nova` primitives, all from the block: `badge`,
  `button`, `card`, `dialog`, `dropdown-menu`, `input`, `label`, `progress`,
  `select`, `separator`, `sheet`, `sidebar`, `skeleton`, `table`, `tabs`,
  `tooltip`. IncidentMind additions were layered on top of shadcn's own files
  (cva variants for status colours, a real heading in `CardTitle`) rather than
  by forking them.
- The sidebar architecture: `SidebarProvider` / collapsible rail / off-canvas
  sheet, `SidebarHeader` / `SidebarContent` / `SidebarFooter`, menu groups,
  keyboard-bound tooltips, and the collapse trigger.
- The shell: `AppShell` lifted out of the block's own `page.tsx` into a shared
  component plus `src/app/(console)/layout.tsx`, so all three routes share one
  sidebar, one `/health` fetch and one `h1` owner.
- The header/`SidebarHeader` structure, the card system, the section rhythm, the
  `[@container]`-query responsive idiom, and the Tailwind v4 `@theme inline` token
  structure.

**Deliberately discarded** (block demo content with no bearing on this product):

- `chart-area-interactive.tsx` and `data-table.tsx` — the block's TanStack v9
  demo table with drag handles, editable cells and a chart drawer. Replaced by a
  hand-rolled read-only table on the same shadcn `Table` primitives: the
  investigation table is a scanner, not a spreadsheet, and none of that
  scaffolding was wanted.
- `nav-documents.tsx`, `nav-secondary.tsx`, `nav-user.tsx` — the sidebar's
  Analytics / Documents / Settings / fake-account entries. The sidebar carries
  IncidentMind's brand and exactly three destinations: **Command Center**,
  **Incidents**, **History**.
- `section-cards.tsx` and `app/dashboard/data.json` — sample analytics cards and
  their fixture data.
- `common/app-header.tsx` — replaced by `site-header.tsx`, which reports real
  provider mode from `/api/health` instead of a version string.

### One deviation, stated plainly

The block's "Recurring patterns" section is **not** reproduced. It is not
computable from this backend: there is no `failure_pattern` field on a stored
experience, and inventing one would be exactly the kind of fabricated signal the
rest of the UI refuses to show. The Organizational Memory panel instead reports
figures that are real — experiences held, external vs local mirror, when the
last one was learned, and provider mode.

### Two fixes to the block's own code

Both were necessary to make the block work with this project's theme, and both
are commented at the site:

1. **Sidebar colour tokens.** The block's `ui/sidebar.tsx` is written against a
   `--sidebar*` token family. Those were not defined in `globals.css`, so
   `bg-sidebar`, `bg-sidebar-accent` and `text-sidebar-foreground` were not
   recognised colour names, Tailwind generated *nothing* for them, and the whole
   nav layer rendered inert — no surface, no hover, no active highlight. The
   family is now defined in `:root`, `.dark` and `@theme inline`.
2. **`data-active` on a boolean.** React stringifies booleans on `data-*`, so
   `data-active={false}` still renders the attribute, and Tailwind v4's
   `data-active:` shorthand matches attribute *presence*. Every nav item
   therefore picked up `data-active:bg-sidebar-accent` and the current page was
   indistinguishable from the rest. The attribute is now omitted when false.

## Running it

The backend must be up first. By default the frontend proxies to
`http://127.0.0.1:8000`.

```bash
cd backend
python -m uvicorn app.main:app --port 8000

cd frontend
npm install
npm run dev
```

Then open http://localhost:3000/dashboard.

If port 8000 is taken on your machine, point the proxy elsewhere without
editing tracked files:

```bash
# frontend/.env.local
API_INTERNAL_URL=http://127.0.0.1:8010
```

## Configuration

| Variable | Where | Meaning |
| --- | --- | --- |
| `API_INTERNAL_URL` | server only | Backend base URL. **Server-side only.** |

The browser never learns the backend's address. Requests go to `/backend/*`,
which `next.config.ts` rewrites to `API_INTERNAL_URL`. That means one origin, no
CORS preflight on the happy path, and no API host baked into the client bundle.

`src/lib/api-server.ts` is marked `server-only` and imports the internal URL;
`src/lib/api-client.ts` binds the same endpoints to `/backend`. If you ever find
yourself wanting to import the server one into a client component, the build will
fail rather than leak the address.

**No credentials belong in this app.** Hindsight and Groq keys live only in the
backend's environment. The browser never sees them and never needs to.

## Architecture

Deliberately no data-fetching library. The reasoning:

- Server components fetch initial data directly (`/dashboard`, `/history`), so
  there is no client-side waterfall on first paint.
- The investigation screen holds its own POST-driven state in a client
  component. The memory panel, the recommendation and the confidence reading all
  come from one response, so they cannot disagree on screen the way they would
  after a `router.refresh()` mid-investigation.
- Mutations call `router.refresh()` only to update *other* server-rendered
  regions (the incident row, the KPI counts).

```
src/
  app/
    (console)/layout.tsx      one sidebar + one /health fetch for every screen
    (console)/dashboard/      server component, parallel fetches
    (console)/incidents/[id]/ server shell + <InvestigationWorkspace/>
    (console)/history/        server component
    fonts/BarberChop.otf      legacy asset; not loaded by the current typography
    robots.ts                 allows /; disallows console and backend paths
  components/
    app-shell.tsx             the block's shell, extracted
    app-sidebar.tsx           brand + three destinations + provider readout
    nav-main.tsx              nav items; "Incidents" anchors to #incidents
    site-header.tsx           brand line + live/demo provider status
    ui/                       the block's shadcn primitives + IncidentMind variants
    common/                   page header, theme toggle, loading/error/empty states
    dashboard/                KPI cards, incident table host, recent learning,
                              memory effect, memory status, demo runner
    incidents/                incident table, incident header, signals,
                              investigation workspace, trigger-similar dialog
    agent/                    investigation progress, recommendation, approval,
                              resolve panel, simulated outcome
    memory/                   the memory panel and per-experience cards
  lib/
    api-core.ts               the only file that knows a URL
    api-server.ts             server-only binding
    api-client.ts             browser binding
    types.ts                  hand-written mirror of the backend schemas
    format.ts                 presentation helpers only
    similar-incidents.ts      the three trigger-similar templates + rotation
    utils.ts                  re-exports `cn` from the `cn` package
  scripts/
    mono_contrast.py          solves the grayscale palette, both themes (see Checks)
    status_contrast.py        the pre-monochrome solver, kept for its validation
    read_lh.py                prints the offending nodes for one LH audit
```

## Design rules

These are constraints, not preferences, and the code follows them deliberately:

1. **No fabricated numbers.** Every figure comes from an endpoint that counts
   real rows. Where the sample behind a mean is empty, the UI says so and shows
   the sample size rather than a flattering zero.
2. **LIVE vs DEMO is never implicit.** The header shows `Memory: live|demo` and
   `Model: live|demo` at all times, sourced from `/api/health`. A judge should
   never have to guess whether a result came from a real service.
3. **Relevance scores are attributed.** Hindsight's recall API returns no
   similarity score, so ours is computed locally. The UI prints `local overlap`
   next to the number. A locally computed score is never presented as if the
   provider produced it.
4. **Withheld ≠ not-searched ≠ empty ≠ unavailable.** The memory panel has four
   distinct states with distinct wording. "Memory was withheld for the control
   run" is not the same claim as "memory has nothing relevant", not the same as
   "no search has run yet", and not the same as "the memory service is down".
   The fourth state exists because an unrun search reporting a negative result
   is a fabricated finding.
5. **No chain-of-thought.** Only `reasoning_summary`, which is written to be
   user-safe. The agent's step list is a timeline of named steps, not its
   internal reasoning.
6. **Nothing executes without approval.** There is no auto-approve path in the
   UI, and the request sends the JSON literal `approved: true` — the UI never
   coerces a loose value into consent. Approval stays blocked once an incident
   is resolved, even though the incident can still be re-investigated, and it
   stays blocked on the memory-OFF control run — approving a counterfactual
   would record a remedy memory never supported, which would then be retained as
   the experience the next incident learns from.
7. **No error produces a blank screen.** Every failure renders a named state
   with the next move. `ApiError` messages never carry stack traces or
   credentials.
8. **Locked blue ramp.** Brand and status styling use `#0A369D`, `#4472CA`,
  `#5E7CE2`, `#92B4F4`, and `#CFDDFE` over light or deep-neutral surfaces.
  Severity and provider states also retain textual labels; colour is never the
  only signal.
9. **Readable states.** Every touch target is at least 24×24px, verified by
   Lighthouse's `target-size` audit, and severity and status always print their
   word so nothing is signalled by shade alone.
10. **No dead controls.** Every rendered button does something. This has been
    the most common defect class found in review: a button whose handler fired
    but whose result was rendered in a different branch, and a button disabled
    by a condition nothing explained.

## Demo flow

`Run learning loop` on the command center executes the backend's deterministic
scenario and reports the real steps, including the recalled incident and the
confidence difference. `Reset demo` restores the seeded state.

To drive it by hand, open an active incident and:

1. `Investigate with memory` — recall happens, recommendation cites an incident.
2. `Compare without memory` — same analyst, history withheld, generic
   recommendation, lower confidence. The delta is shown side by side.
3. `Approve simulated action` — requires typing an approver; returns
   before/after telemetry.
4. `Resolve and retain` — pre-filled from the agent's own output, editable.
5. `Trigger a similar incident` — a new incident on the same service in
   different words; investigating it recalls the experience just retained.

Step 5's wording is a fixed demonstration phrasing, labelled as such in the
dialog. It deliberately avoids the original incident's vocabulary so retrieval
has to match on failure shape rather than shared keywords.

Steps 1–2 also work on an incident that is already resolved, which is how the
loop is demonstrated from a closed incident: its experience is in memory, and
re-investigating it is how you confirm the recall is real. Approval and
retention stay disabled there, because there is nothing left to approve.

## Colour

**One blue, in five steps.** The palette:

```
#CFDDFE   #92B4F4   #5E7CE2   #4472CA   #0A369D
```

Every token in `globals.css` is that single hue (~264°) with only lightness and
chroma varying. There is no second colour anywhere in the interface, so the
palette cannot drift — no accent hue to clash with the brand, no status hue to
argue with it, because they are all the same blue. `--destructive` is deep blue
rather than red for the same reason.

The surfaces form one ladder, each step 2–3% off the last, so panels separate by
tone rather than by outline:

```
page 0.972  ->  card / sidebar / popover 0.995
muted 0.952  ->  secondary 0.945  ->  accent 0.935
sidebar-accent 0.925  ->  border 0.895
```

The panels stay almost white (chroma 0.004–0.022). The tint lives in the gaps and
the borders, not in the cards — white cards on a blue-tinted page still read as
raised paper, whereas saturated panels would make this look like a product site
rather than an operations console.

### Severity is blue depth

Blue is monotone in lightness, so depth maps onto urgency directly: the darkest
blue is the most urgent. A glance down the incidents table orders the rows, which
is something the previous zero-chroma palette could not do — see below. The
severity steps also get an evenly stepped wash alpha reinforcing the same order:

| | critical | high | medium | low |
|---|---|---|---|---|
| wash alpha | 20% | 17% | 14% | 11% |

The status *text* colours are compressed into a narrow `0.360–0.470` band, and
that is still a forced constraint rather than a taste call: contrast falls as
lightness rises, so spreading them wider put `low` at 4.16:1 on the first attempt.
Hue is what buys the room — it lets the text be dark *and* the fill stay strong,
whereas a zero-chroma ramp has to choose. Every badge also prints its severity
word, so nothing depends on the shade alone.

`python scripts/blue_contrast.py` converts the five hexes, re-derives the whole
table, and prints it. Worst cases are **5.16–6.80:1** in light and
**5.16–5.49:1** in dark, measured against the worst surface a badge actually
lands on — the wash composited over the surface, which is darker than the card, so
the naive "does it pass on white" check overstates it. The alpha values in
`badge.tsx` are load-bearing: changing one changes the background its text sits
on.

`scripts/mono_contrast.py` is the grayscale solver this replaced and
`scripts/status_contrast.py` the one before it. Both are kept because they
document *why* the ramp is shaped the way it is, and `blue_contrast.py` reuses
their validated oklch→sRGB path.

### Light and dark

Both palettes are in `globals.css` as CSS custom properties, switched by a `dark`
class on `<html>`. `ThemeToggle` in the header sets it.

The class is applied by a tiny inline script in `layout.tsx` rather than by a
component effect, because an effect runs after paint and shows as a white flash
on a dark theme. The script and the component read the same `localStorage` key
and apply the same rule, so they cannot disagree.

**Light is the default, and the OS setting is deliberately not consulted.** The
interface is built as white and light gray; following `prefers-color-scheme` meant
anyone whose OS was set to dark landed on the inverted palette instead. The dark
palette is a neutral-gray inversion of the same ladder and is one click away for
a dark room. To restore OS-following, change `preferredTheme` *and*
`themeBootstrapScript` together — they have to stay rule-for-rule identical or
the page flashes.

The button's accessible name states the scheme it will switch *to*, not the
current one, so it is never ambiguous.

## Typography

DM Sans is loaded with `next/font/google` and applied globally across the
landing page, navbar, dashboard, incident screens, headings, and controls.
Roboto Mono remains available for incident IDs and technical values. The
Barber Chop font file is a legacy asset and is not loaded by the application.

## Checks

```bash
npm run lint        # eslint .
npm run typecheck   # tsc --noEmit
npm run build       # production build

python scripts/mono_contrast.py      # the grayscale palette, both themes
python scripts/status_contrast.py    # the pre-monochrome tokens, kept for history
```

> Do not run `npm run build` while `npm run dev` is running. They share
> `.next/`, and the build overwrites the dev server's chunks underneath it,
> leaving stale `vendor-chunks/*` references and 500s. Stop the dev server
> first, or `rm -rf .next` if it already happened.

**Accessibility.** Lighthouse is the gate, on all three routes in **both**
themes, against the production build. The incident page is audited in its
richest state — investigated *and* memory-compared — not just its empty state,
because that is where the dense layouts live. All six audits score 1.0 for
accessibility, best-practices and SEO with no failing audit. Lighthouse applies
mobile emulation, so it also covers touch-target size, which is the failure mode
a desktop-only check would miss.

Three real defects were caught this way and would not have been caught by reading
the code: two incident-id links at 23.7px tall (a `py-1` / `-my-1` pair that
cancelled exactly), badge text at 3.6–4.4:1 because the tinted badge background is
darker than the card the tokens were tuned against, and an unmet-step label at
3.6:1 from `text-muted-foreground/70` in dark mode.

**Responsive.** Verified at 360 / 390 / 640 / 768 / 1024 / 1280 / 1536 / 1920 by
loading the routes in a sized iframe and reading computed layout, since there is
no viewport-resize control here. At every width: zero page-level horizontal
overflow, header and body column counts in agreement, the table a real
`overflow-x: auto` container rather than clipped cells, and nothing clipped
outside it. Below 768px the sidebar collapses to a sheet and the table drops to
five columns; at 768–1023px the sidebar is inline, so the table is narrower
there than at either side of that breakpoint and needs a swipe — which is why
the Columns menu exists. The incident workspace is one column below its
container-query breakpoint and two above it, and `/incidents/[id]` and
`/history` both have zero overflow at 390px.

There is no frontend unit test suite. The backend has 87 tests plus two
verification gates (`scripts/verify_learning_loop.py`,
`scripts/verify_http_server.py`), and the frontend is verified by driving these
screens against the live backend.

### A note on verifying contrast

Do not hand-roll a contrast checker over `getComputedStyle` in the browser.
`oklch()` values have to be converted, and semi-transparent backgrounds
(`bg-status-critical/22`) have to be composited over their real ancestors. Both
steps are easy to get subtly wrong in a way that produces confident, wrong numbers
— that happened here, and briefly suggested dark mode was unreadable when it was
fine.

`scripts/mono_contrast.py` does the arithmetic offline instead, and is worth
keeping for two reasons. It converts oklch → sRGB in a way that was **validated
against the exact hex pairs Lighthouse reported** (`high` reproduced to the byte),
so its output can be trusted rather than merely plausible. And it solves for
lightness against the *worse* of the surfaces a badge can land on, targeting
5.0:1 so that compositing rounding cannot push a value back under 4.5:1. It
prints both themes, so a token change that fixes light and breaks dark is
visible immediately.

`scripts/status_contrast.py` is the earlier, hue-carrying version of the same
check. It is kept because its validation block is what proved the oklch → sRGB
path agrees with the browser, and that validation is inherited by the
monochrome script. It no longer describes the shipped palette.

Lighthouse remains the gate. The script exists to choose the values; the audit
decides whether they worked.
