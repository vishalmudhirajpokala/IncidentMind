import { BrainIcon } from "lucide-react";

import { formatRelative, providerSummary } from "@/lib/format";
import type { HealthResponse, MemoryEvent, MetricsOverview } from "@/lib/types";

/**
 * "Organizational Memory" — a compact status readout, not a dashboard of its own.
 *
 * Every figure is counted from real rows. The brief asked for a recurring-pattern
 * count here; the backend does not compute one, and inferring "recurring patterns"
 * from experience titles would be a guess dressed as a metric. So the slot is
 * filled with facts the API does report: how many experiences exist, where they
 * actually live, when the last one was learned, and which provider is answering.
 */
export function MemoryStatus({
  metrics,
  learning,
  health,
}: {
  metrics: MetricsOverview;
  learning: MemoryEvent[];
  health: HealthResponse | null;
}) {
  const lastLearned = learning
    .map((event) => event.retained_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);

  return (
    <section
      aria-labelledby="organizational-memory"
      className="evidence-edge flex h-full flex-col gap-2 rounded-lg border bg-card px-3 py-2.5"
    >
      <div className="flex items-center justify-between gap-2">
        <h2
          id="organizational-memory"
          className="flex items-center gap-1.5 text-sm font-medium"
        >
          <BrainIcon className="size-3.5 text-muted-foreground" aria-hidden />
          Organizational memory
        </h2>
        <span className="text-xs text-muted-foreground">
          {metrics.memory_events_total} experiences
        </span>
      </div>

      <dl className="grid gap-1 text-xs">
        <div className="flex items-baseline justify-between gap-3">
          <dt className="text-muted-foreground">Retained externally</dt>
          <dd className="tabular font-medium">{metrics.memory_events_external}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-3">
          <dt className="text-muted-foreground">Held in the local mirror</dt>
          <dd className="tabular font-medium">{metrics.memory_events_local_only}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-3">
          <dt className="text-muted-foreground">Last learned</dt>
          <dd className="font-medium">
            {formatRelative(lastLearned ?? null) ?? "Nothing retained yet"}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-3">
          <dt className="text-muted-foreground">Answering with</dt>
          <dd className="font-medium">{providerSummary(health?.memory)}</dd>
        </div>
      </dl>
    </section>
  );
}
