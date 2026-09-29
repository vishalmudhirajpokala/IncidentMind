import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDuration } from "@/lib/format";
import type { MetricsOverview } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * The four operational figures.
 *
 * This is the dashboard-01 section-card layout — description label, large value,
 * footer with a primary and a secondary line — pointed at real data. Every number
 * here is counted from real rows by `/api/metrics/overview`. Where the sample
 * behind a figure is empty the card says so rather than showing a flattering
 * zero, and the mean resolution time always shows its sample size. The stock
 * template's "+12.5%" trend badges are gone: there is no honest way to produce
 * them here, and a fabricated delta is worse than no delta.
 */

interface Kpi {
  label: string;
  value: string;
  /** The footer's emphasised line. */
  headline: string;
  /** The footer's supporting line. */
  detail: string;
  tone?: "default" | "muted";
}

function KpiCard({ kpi }: { kpi: Kpi }) {
  return (
    <Card className="@container/card">
      <CardHeader>
        <CardDescription>{kpi.label}</CardDescription>
        <CardTitle
          className={cn(
            // `data-figure` puts the number in the display face. `tabular` is
            // dropped: Barber Chop is a proportional face, so `tabular-nums` is
            // inert here, and these values are standalone rather than stacked in
            // a column that needs to hold still.
            "text-2xl @[250px]/card:text-3xl",
            kpi.tone === "muted" && "text-muted-foreground",
          )}
          data-figure
        >
          {kpi.value}
        </CardTitle>
      </CardHeader>
      <CardFooter className="flex-col items-start gap-1 text-sm">
        <div className="line-clamp-1 font-medium">{kpi.headline}</div>
        <div className="text-muted-foreground">{kpi.detail}</div>
      </CardFooter>
    </Card>
  );
}

export function KpiCards({ metrics }: { metrics: MetricsOverview }) {
  const resolution = metrics.average_resolution_time_seconds;
  const sample = metrics.incidents_with_measured_resolution;

  const kpis: Kpi[] = [
    {
      label: "Active incidents",
      value: String(metrics.incidents_active),
      headline:
        metrics.incidents_active === 1 ? "1 incident open" : `${metrics.incidents_active} incidents open`,
      detail: `${metrics.incidents_total} recorded in total`,
    },
    {
      label: "Incidents resolved",
      value: String(metrics.incidents_resolved),
      headline: `${metrics.investigations_total} investigations run`,
      detail: `${metrics.investigations_memory_on} with memory, ${metrics.investigations_memory_off} without`,
    },
    {
      label: "Avg. resolution time",
      value: formatDuration(resolution),
      tone: resolution === null ? "muted" : "default",
      headline:
        sample === 0
          ? "No measured resolutions yet"
          : `Mean of ${sample} measured resolution${sample === 1 ? "" : "s"}`,
      detail: "Unresolved incidents are excluded, not counted as zero",
    },
    {
      label: "Experiences in memory",
      value: String(metrics.memory_events_total),
      headline:
        metrics.memory_events_external > 0
          ? `${metrics.memory_events_external} retained externally`
          : "Held in the local mirror",
      detail:
        metrics.memory_events_external > 0
          ? `${metrics.memory_events_local_only} more in the local mirror`
          : "Nothing has been written to an external provider",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 @5xl/main:grid-cols-4">
      {kpis.map((kpi) => (
        <KpiCard key={kpi.label} kpi={kpi} />
      ))}
    </div>
  );
}
