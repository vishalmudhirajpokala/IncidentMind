"use client";

import * as React from "react";
import Link from "next/link";
import { BrainIcon, ChevronDownIcon, DatabaseIcon, EyeOffIcon, TriangleAlertIcon } from "lucide-react";

import { EmptyState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatPercent } from "@/lib/format";
import type { MemoryEvidence, ProviderStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Relevant Memory.
 *
 * This is the panel that has to make one point unmissable: the recommendation
 * is not free-floating opinion, it is a citation. Every card therefore leads
 * with the historical incident id and the reason it was retrieved, and always
 * exposes root cause, the action that worked, and the outcome.
 *
 * `relevance` is only rendered when the provider actually returned one. When
 * it was computed locally the method is printed next to it, so a number is
 * never presented as though Hindsight produced it.
 */
export function MemoryPanel({
  evidence,
  provider,
  status,
  detail,
  query,
  loading,
  memoryEnabled = true,
  searched = true,
}: {
  evidence: MemoryEvidence[];
  provider?: ProviderStatus | null;
  status?: string;
  detail?: string | null;
  query?: string | null;
  loading?: boolean;
  memoryEnabled?: boolean;
  /**
   * Whether a run has actually queried memory yet.
   *
   * Without this the panel cannot tell "the search found nothing" apart from
   * "no search has happened", and defaults to the former — so opening a
   * never-investigated incident used to claim that organisational memory had
   * been searched and found nothing resembling it. An unrun search reporting a
   * negative result is exactly the kind of invented finding this UI must not
   * make.
   */
  searched?: boolean;
}) {
  // Four genuinely different states, which must never share wording:
  //   idle      - no investigation has run, so memory has not been consulted yet
  //   withheld  - the control run; memory was not consulted (not an outage)
  //   degraded  - the service was asked and did not answer
  //   empty     - the service was asked and had nothing relevant
  const idle = !searched;
  const withheld = !idle && (!memoryEnabled || status === "disabled");
  const degraded = !withheld && (status === "degraded" || provider?.available === false);
  const empty = !withheld && !degraded && evidence.length === 0;

  const badge = idle
    ? { variant: "muted" as const, text: "Not searched" }
    : withheld
    ? { variant: "muted" as const, text: "Not consulted" }
    : degraded
      ? { variant: "critical" as const, text: "Unavailable" }
      : provider?.mode === "live"
        ? { variant: "live" as const, text: "Hindsight" }
        : provider?.mode === "demo"
          ? { variant: "demo" as const, text: "Local mirror" }
          : { variant: "muted" as const, text: "No provider" };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-1.5">
          <BrainIcon className="size-3.5 text-muted-foreground" />
          Relevant memory
        </CardTitle>
        <Badge variant={badge.variant}>{badge.text}</Badge>
      </CardHeader>

      <CardContent className="space-y-3">
        {!idle && !withheld && !degraded && !empty ? (
          <div className="flex items-baseline justify-between gap-2 border-b pb-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Prior experiences found
            </p>
            <p className="text-sm font-medium">{evidence.length}</p>
          </div>
        ) : null}
        {loading ? (
          <div className="space-y-2">
            {[0, 1].map((i) => (
              <div key={i} className="h-28 animate-pulse rounded-md bg-muted" />
            ))}
          </div>
        ) : idle ? (
          <EmptyState
            title="Not searched yet"
            message="Memory is queried as part of an investigation run. Nothing has been searched for this incident, so there is nothing to report either way."
          />
        ) : withheld ? (
          <div className="rounded-r-md border-l-3 border-muted-foreground/40 bg-muted/50 py-2.5 pl-3 pr-3">
            <div className="flex items-center gap-1.5">
              <EyeOffIcon className="size-3.5 text-muted-foreground" />
              <p className="text-xs font-medium">Memory withheld for this run</p>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              This is the control path: the same analyst ran on the same incident with history
              withheld, so any difference in the recommendation is attributable to memory and
              nothing else. Switch to &ldquo;With memory&rdquo; to see the comparison.
            </p>
          </div>
        ) : degraded ? (
          <div className="rounded-r-md border-l-3 border-destructive bg-destructive/5 py-2.5 pl-3 pr-3">
            <div className="flex items-center gap-1.5">
              <TriangleAlertIcon className="size-3.5 text-destructive" />
              <p className="text-xs font-medium">Memory service unavailable</p>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              {detail ??
                "The external memory service did not answer, so the recommendation below is based on current signals only."}
            </p>
          </div>
        ) : empty ? (
          <EmptyState
            title="Searched, nothing relevant"
            message="Organisational memory was searched and returned nothing resembling this incident. The recommendation below is derived from the current signals alone, and says so."
          />
        ) : (
          <>
            <ol className="space-y-2">
              {evidence.map((item) => (
                <MemoryCard key={item.memory_id} item={item} />
              ))}
            </ol>

            <WhyThisMatters evidence={evidence} />
          </>
        )}

        {query ? (
          <details className="border-t pt-2">
            <summary className="cursor-pointer text-[11px] text-muted-foreground hover:text-foreground">
              Memory query sent ({evidence.length} result{evidence.length === 1 ? "" : "s"})
            </summary>
            <pre className="mt-1.5 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-muted/60 p-2 font-mono text-[10px] leading-relaxed text-muted-foreground">
              {query}
            </pre>
          </details>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function MemoryCard({ item }: { item: MemoryEvidence }) {
  const [open, setOpen] = React.useState(false);
  const relevance = item.relevance;

  return (
    <li className="evidence-edge overflow-hidden rounded-r-md bg-muted/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-start justify-between gap-2 px-3 py-2.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
      >
        <div className="min-w-0 space-y-1.5">
          <div className="flex flex-wrap items-center gap-1.5">
            {item.source_incident_id ? (
              <Link
                href={`/incidents/${item.source_incident_id}`}
                onClick={(event) => event.stopPropagation()}
                className="inline-flex min-h-6 items-center py-1 font-mono text-[11px] font-semibold hover:underline"
              >
                {item.source_incident_id}
              </Link>
            ) : (
              <span className="font-mono text-[11px] font-semibold">local experience</span>
            )}
            {item.historical_service ? (
              <Badge variant="outline">{item.historical_service}</Badge>
            ) : null}
          </div>

          {item.historical_title ? (
            <p className="line-clamp-1 text-xs font-medium">{item.historical_title}</p>
          ) : null}

          <p className="line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
            {item.why_relevant}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          {relevance !== null && relevance !== undefined ? (
            <span className="text-right">
              <span data-figure className="block text-sm leading-none">
                {formatPercent(relevance, 0)}
              </span>
              <span className="block text-[10px] text-muted-foreground">
                {relevanceLabel(item.relevance_method)}
              </span>
            </span>
          ) : (
            <span className="text-[10px] text-muted-foreground">no score</span>
          )}
          <ChevronDownIcon
            className={cn("size-3.5 text-muted-foreground transition-transform", open && "rotate-180")}
          />
        </div>
      </button>

      {relevance !== null && relevance !== undefined ? (
        <Progress
          value={Math.round(relevance * 100)}
          className="h-0.5 rounded-none [&>div]:bg-status-live"
        />
      ) : null}

      {open ? (
        <div className="space-y-2.5 border-t bg-card/60 px-3 py-2.5 text-xs">
          <Field label="Why relevant" value={item.why_relevant} />
          <Field label="Historical root cause" value={item.historical_root_cause} />
          <Field label="What worked" value={item.historical_action} />
          <Field label="Outcome" value={item.historical_outcome} />
          <Field label="Lesson retained" value={item.historical_lesson} />

          {item.matched_on.length > 0 ? (
            <div className="space-y-1">
              <p className="text-[11px] font-medium text-muted-foreground">Matched on</p>
              <ul className="space-y-0.5">
                {item.matched_on.slice(0, 3).map((reason) => (
                  <li key={reason} className="flex gap-1.5 text-[11px] text-muted-foreground">
                    <span aria-hidden className="mt-1.5 size-1 shrink-0 rounded-full bg-status-live/70" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="flex items-center gap-1.5 border-t pt-2 text-[10px] text-muted-foreground">
            <DatabaseIcon className="size-3" />
            Retrieved from {item.provider}
          </p>
        </div>
      ) : null}
    </li>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="space-y-0.5">
      <p className="text-[11px] font-medium text-muted-foreground">{label}</p>
      <p className="leading-relaxed">{value}</p>
    </div>
  );
}

/**
 * The synthesis across all recalled memories, not a repeat of the top card.
 * The backend already composes this from the evidence, so it is shown as
 * given rather than recomputed here.
 */
function WhyThisMatters({ evidence }: { evidence: MemoryEvidence[] }) {
  if (evidence.length === 0) return null;

  const top = evidence[0];
  if (!top) return null;

  return (
    <div className="evidence-edge rounded-r-md bg-status-live/8 py-2.5 pl-3 pr-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        Why this memory matters
      </p>
      <p className="mt-1 text-xs leading-relaxed">
        {evidence.length === 1
          ? `One prior experience on this service matches. Its recorded remedy already worked once, on ${top.source_incident_id ?? "a previous incident"}.`
          : `${evidence.length} prior experiences match. ${top.source_incident_id ?? "The closest"} is the strongest match; the recommendation reuses a remedy that has already succeeded on this service.`}
      </p>
    </div>
  );
}

/**
 * Names the scoring method honestly. A number computed by this application is
 * never allowed to look like a score the memory service returned.
 */
function relevanceLabel(method: string | null | undefined): string {
  switch (method) {
    case "local_lexical_overlap":
      return "local overlap";
    case "provider_score":
      return "provider";
    default:
      return "relevance";
  }
}
