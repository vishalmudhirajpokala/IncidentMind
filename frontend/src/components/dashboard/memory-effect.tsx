import { BrainIcon, GitCompareArrowsIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatPercent } from "@/lib/format";
import type { MetricsOverview } from "@/lib/types";

/**
 * What memory changed, measured.
 *
 * Both numbers are averages over investigations that actually ran in this
 * deployment — one set with memory, one without — so the comparison is a real
 * observation and not a claim. The panel says plainly how small the sample is,
 * because a mean over two runs should not be read like a benchmark.
 */
export function MemoryEffect({ metrics }: { metrics: MetricsOverview }) {
  const on = metrics.investigations_memory_on;
  const off = metrics.investigations_memory_off;
  const onConfidence = metrics.average_confidence_memory_on;
  const offConfidence = metrics.average_confidence_memory_off;

  const recurring = Object.entries(metrics.by_service)
    .filter(([, count]) => count > 1)
    .sort((a, b) => b[1] - a[1]);

  const sample = on + off;
  const comparable = onConfidence !== null && offConfidence !== null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-1.5">
          <GitCompareArrowsIcon className="size-3.5 text-muted-foreground" />
          What memory changed
        </CardTitle>
        <Badge variant="muted">n={sample} investigation{sample === 1 ? "" : "s"}</Badge>
      </CardHeader>

      <CardContent className="space-y-3">
        {comparable ? (
          <div className="space-y-2.5">
            <ConfidenceRow
              label="Memory on"
              value={onConfidence ?? 0}
              count={on}
              tone="live"
            />
            <ConfidenceRow
              label="Memory off"
              value={offConfidence ?? 0}
              count={off}
              tone="muted"
            />
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            Not enough investigations yet. Run an incident with memory on and again with memory
            off, and the two confidences will be compared here.
          </p>
        )}

        <dl className="grid grid-cols-2 gap-x-3 gap-y-2 border-t pt-3 text-xs">
          <div>
            <dt className="text-muted-foreground">Memory-backed investigations</dt>
            <dd className="tabular mt-0.5 font-medium">
              {on} of {sample}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Experiences retained</dt>
            <dd className="tabular mt-0.5 font-medium">{metrics.memory_events_total}</dd>
          </div>
          <div className="col-span-2">
            <dt className="text-muted-foreground">Recurring patterns (services with &gt;1 incident)</dt>
            <dd className="mt-1 flex flex-wrap gap-1">
              {recurring.length === 0 ? (
                <span className="text-muted-foreground">None observed</span>
              ) : (
                recurring.map(([name, count]) => (
                  <Badge key={name} variant="outline">
                    <BrainIcon />
                    {name} ×{count}
                  </Badge>
                ))
              )}
            </dd>
          </div>
        </dl>

        <p className="border-t pt-2 text-[11px] leading-relaxed text-muted-foreground">
          Measured across investigations run in this deployment. It is an observation of these
          runs, not a benchmark, and the sample above is the whole sample.
        </p>
      </CardContent>
    </Card>
  );
}

function ConfidenceRow({
  label,
  value,
  count,
  tone,
}: {
  label: string;
  value: number;
  count: number;
  tone: "live" | "muted";
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="text-muted-foreground">
          {/* The sample size is the honest part of this reading, so it is not
              faded for looks: at 70% opacity it fell to 3.6:1 on the dark
              card. The parentheses already mark it as a qualifier. */}
          {label} <span>(n={count})</span>
        </span>
        <span data-figure className="text-sm">
          {formatPercent(value)}
        </span>
      </div>
      <Progress
        value={Math.round(value * 100)}
        className={tone === "muted" ? "[&>div]:bg-muted-foreground/40" : "[&>div]:bg-status-live"}
      />
    </div>
  );
}
