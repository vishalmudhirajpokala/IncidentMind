import { PackageIcon, GitCommitVerticalIcon, RadioIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { metric } from "@/lib/format";
import type { Incident } from "@/lib/types";

/**
 * Current signals.
 *
 * Reads from the incident's free-form metrics bag rather than assuming fixed
 * key names, and silently omits anything the caller did not supply. A panel
 * that shows "—" for a metric nobody reported is worse than one that shows
 * only what is real.
 */
export function SignalsPanel({ incident }: { incident: Incident }) {
  const known = [
    metric(incident, ["error_rate", "errorRate", "failure_rate", "failureRate"]),
    metric(incident, ["p99_latency_ms", "p99LatencyMs", "latency_ms", "latencyMs"]),
    metric(incident, ["pool_utilization", "poolUtilization", "cpu_utilization", "db_pool_used"]),
    metric(incident, ["requests_per_second", "rps", "request_rate", "throughput"]),
  ].filter((m): m is { label: string; value: string } => m !== null);

  const signals = incident.signals ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-1.5">
          <RadioIcon className="size-3.5 text-muted-foreground" />
          Current signals
        </CardTitle>
        {incident.deployment_version ? (
          <Badge variant="outline">
            <GitCommitVerticalIcon />
            {incident.deployment_version}
          </Badge>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-4">
        {known.length > 0 ? (
          <dl className="grid grid-cols-2 gap-x-3 gap-y-3 sm:grid-cols-4">
            {known.map((m) => (
              <div key={m.label} className="rounded-md border bg-muted/30 p-3">
                <dt className="truncate text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  {m.label}
                </dt>
                <dd data-figure className="mt-1.5 text-lg leading-none">
                  {m.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}

        {(signals.length > 0 || incident.recent_change) && (
          <div className="space-y-2 border-t pt-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Key indicators
            </p>
            <ul className="space-y-1.5 text-xs text-muted-foreground">
              {signals.slice(0, 4).map((signal, index) => (
                <li key={index} className="flex gap-2">
                  <span aria-hidden className="mt-1.5 size-1.5 shrink-0 rounded-full bg-status-live" />
                  <span className="leading-relaxed text-foreground">{signal}</span>
                </li>
              ))}
              {incident.recent_change ? (
                <li className="flex gap-2">
                  <PackageIcon className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                  <span className="leading-relaxed text-foreground">{incident.recent_change}</span>
                </li>
              ) : null}
            </ul>
          </div>
        )}

        {known.length === 0 && signals.length === 0 && !incident.recent_change ? (
          <p className="text-xs text-muted-foreground">
            No signals or metrics were recorded with this incident.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
