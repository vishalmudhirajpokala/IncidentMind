import Link from "next/link";
import { ArrowUpRightIcon } from "lucide-react";

import { EmptyState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  experienceErrorRate,
  experienceHeadline,
  experienceOutcome,
  experienceService,
  formatRelative,
} from "@/lib/format";
import type { MemoryEvent } from "@/lib/types";

/**
 * "Recent Learning" — the last few retained experiences.
 *
 * Deliberately not a memory dashboard. This is the same content the operator
 * will meet inside an investigation, surfaced on the command center so the
 * system is visibly accumulating experience. It shows what was learned, not
 * analytics about the memory store.
 */
export function RecentLearning({ events }: { events: MemoryEvent[] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle>Recent learning</CardTitle>
        <Badge variant="muted">{events.length} shown</Badge>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {events.length === 0 ? (
          <EmptyState
            title="No experience retained yet"
            message="Resolve an incident with a recorded root cause and the agent will keep the outcome, so the next similar incident can start from it."
          />
        ) : (
          events.map((event) => {
            const service = experienceService(event);
            const outcome = experienceOutcome(event);
            const errorRate = experienceErrorRate(event);
            const headline = experienceHeadline(event);

            return (
              <div
                key={event.id}
                className="evidence-edge rounded-r-md bg-muted/40 py-2 pl-3 pr-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Link
                        href={event.incident_id ? `/incidents/${event.incident_id}` : "/history"}
                        // Same reasoning as the memory panel's id link: `py-1` and
                        // `-my-1` cancelled out and left the target under 24px.
                        className="inline-flex min-h-6 items-center gap-0.5 py-1 font-mono text-[11px] font-semibold hover:underline"
                      >
                        {event.incident_id ?? "local"}
                        <ArrowUpRightIcon className="size-3 opacity-60" />
                      </Link>
                      {service ? <Badge variant="outline">{service}</Badge> : null}
                      <span className="text-[11px] text-muted-foreground">
                        {formatRelative(event.retained_at)}
                      </span>
                    </div>

                    <p className="line-clamp-2 text-xs leading-relaxed">{headline}</p>

                    {outcome ? (
                      <p className="line-clamp-1 text-[11px] text-muted-foreground">
                        <span className="font-medium text-foreground">Outcome:</span> {outcome}
                      </p>
                    ) : null}
                    {errorRate ? (
                      <p className="text-[11px] text-muted-foreground">{errorRate}</p>
                    ) : null}
                  </div>

                  <Badge
                    variant={event.external_retained ? "live" : "demo"}
                    className="mt-0.5 shrink-0"
                    title={
                      event.external_retained
                        ? "Written to the external memory service"
                        : "Held only in the local mirror"
                    }
                  >
                    {event.external_retained ? "External" : "Local"}
                  </Badge>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
