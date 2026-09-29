/**
 * Simulated phrasings for "trigger a similar incident".
 *
 * These are demonstration inputs, and that is all they are: canned customer
 * reports used to show that a retained experience is retrieved for an incident
 * worded differently from the one it was learned from. They are not synthetic
 * telemetry and nothing in the UI presents them as real observations.
 *
 * The wording deliberately avoids the vocabulary the original incident used
 * (no "5xx", no "pool", no "exhausted"), which is the point: a lexical
 * retriever has to bridge the gap on the failure shape, not on shared keywords.
 */

export interface SimilarIncidentTemplate {
  id: string;
  title: string;
  description: string;
  signals: string[];
}

export const SIMILAR_INCIDENT_TEMPLATES: SimilarIncidentTemplate[] = [
  {
    id: "customer-complaint",
    title: "Customers report the basket flow stalls before payment",
    description:
      "Support is receiving complaints that shoppers cannot complete an order. The requests appear to hang rather than fail, and the on-call dashboard shows a much longer tail on end-to-end timing than usual. A build was promoted shortly before the first report.",
    signals: [
      "order completion attempts stalling",
      "tail response time far above the usual range",
      "a release was promoted minutes before the first report",
    ],
  },
  {
    id: "synthetic-monitor",
    title: "Availability synthetic check flapping on the order path",
    description:
      "The synthetic availability probe for the ordering path is alternating between pass and timeout. Traffic to the datastore looks saturated from the service side. The most recent deploy to the ordering service is a small patch, and the flapping started almost immediately after it.",
    signals: [
      "availability probe alternating pass/timeout",
      "datastore appearing saturated from the service side",
      "flapping began within minutes of a patch deploy",
    ],
  },
  {
    id: "capacity-alert",
    title: "Saturation alert on the ordering service datastore client",
    description:
      "The saturation alert fired for the ordering service. Every connection the service is permitted to open is in use, and requests queue rather than erroring outright, which is why the error ratio looks moderate while customers are still affected. The release that shipped just before the alert changed how work is scheduled.",
    signals: [
      "all permitted datastore connections in use",
      "requests queueing rather than erroring",
      "error ratio moderate while customers are still affected",
      "scheduling change in the preceding release",
    ],
  },
];

export function nextTemplate(index: number): SimilarIncidentTemplate {
  return (
    SIMILAR_INCIDENT_TEMPLATES[index % SIMILAR_INCIDENT_TEMPLATES.length] ??
    SIMILAR_INCIDENT_TEMPLATES[0]!
  );
}

const LAST_USED_KEY = "incidentmind-last-similar-template";

/**
 * Picks the phrasing to open the dialog on, and remembers it.
 *
 * Always starting at index 0 meant that triggering twice in a row produced two
 * incidents with byte-identical text, which quietly undoes the point of the
 * button: the new incident has to be worded *differently* from the one the
 * experience was learned from, and from the last one created, or "recall works
 * across different wording" is being demonstrated against identical wording.
 *
 * `sessionStorage` rather than `localStorage`, so the rotation is per working
 * session and does not follow someone around between days. If storage is
 * unavailable this degrades to index 0, which is the old behaviour.
 */
export function takeNextTemplateId(): string {
  const first = SIMILAR_INCIDENT_TEMPLATES[0]!.id;
  if (typeof window === "undefined") return first;

  let last = "";
  try {
    last = window.sessionStorage.getItem(LAST_USED_KEY) ?? "";
  } catch {
    return first;
  }

  const lastIndex = SIMILAR_INCIDENT_TEMPLATES.findIndex((t) => t.id === last);
  const next =
    SIMILAR_INCIDENT_TEMPLATES[
      (lastIndex + 1 + SIMILAR_INCIDENT_TEMPLATES.length) % SIMILAR_INCIDENT_TEMPLATES.length
    ]!;

  try {
    window.sessionStorage.setItem(LAST_USED_KEY, next.id);
  } catch {
    // The rotation is a nicety; failing to persist it must not break the dialog.
  }

  return next.id;
}

/**
 * Index of a template id in the list, for opening the dialog on a known one.
 */
export function templateIndexById(id: string): number {
  const index = SIMILAR_INCIDENT_TEMPLATES.findIndex((t) => t.id === id);
  return index < 0 ? 0 : index;
}

/**
 * Bumps the patch component of a version string so the "similar" incident is
 * plainly a later release than the one it is meant to resemble.
 */
export function nextVersion(current: string | null | undefined): string {
  const match = /v?(\d+)\.(\d+)\.(\d+)/.exec(current ?? "");
  if (!match) return "v1.0.0";
  const [, major, minor, patch] = match;
  return `v${major}.${minor}.${Number(patch ?? 0) + 1}`;
}
