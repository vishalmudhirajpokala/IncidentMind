import { ShieldCheckIcon, TriangleAlertIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { InvestigationResult } from "@/lib/types";

const RISK_VARIANT = {
  low: "ok",
  medium: "demo",
  high: "critical",
} as const;

/**
 * The recommendation, with the evidence behind it made countable.
 *
 * "Evidence count" here is the number of recalled experiences that support the
 * call, which is a real number from the response. "Historical support" states
 * whether that remedy has actually been used successfully before. Both are
 * shown as 0 / "none" when absent rather than being softened into vagueness.
 */
export function RecommendationCard({ result }: { result: InvestigationResult }) {
  const action = result.recommended_action;
  const support = result.memory_evidence.filter((m) => m.historical_action).length;

  if (!action) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recommended action</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            The agent did not produce a recommended action for this incident.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={result.memory_enabled ? "evidence-edge rounded-l-none" : undefined}>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <CardTitle>Recommended action</CardTitle>
        <div className="flex items-center gap-1.5">
          <Badge variant="muted">Simulation</Badge>
          <Badge variant={RISK_VARIANT[action.risk]}>Risk: {action.risk}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="rounded-md border bg-muted/30 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Recommended action
          </p>
          <p className="mt-2 text-lg leading-snug">{action.action}</p>
        </div>

        <p className="text-sm leading-relaxed text-muted-foreground">{action.reason}</p>

        <dl className="grid grid-cols-2 gap-2 border-t pt-3 text-xs">
          <div className="rounded-md bg-muted/20 p-2.5">
            <dt className="text-muted-foreground">Evidence</dt>
            <dd className="mt-1 font-medium">
              {result.memory_count} prior experience{result.memory_count === 1 ? "" : "s"}
            </dd>
          </div>
          <div className="rounded-md bg-muted/20 p-2.5">
            <dt className="text-muted-foreground">History</dt>
            <dd className="mt-1 font-medium">
              {support > 0 ? "Previous remedy succeeded" : "No prior use recorded"}
            </dd>
          </div>
        </dl>

        <p className="flex items-start gap-1.5 rounded-r-md border-l-2 border-status-demo bg-status-demo/8 py-2 pl-2.5 text-xs leading-relaxed">
          <TriangleAlertIcon className="mt-0.5 size-3.5 shrink-0 text-status-demo" />
          <span>Simulation only — no production infrastructure is contacted.</span>
        </p>

        {result.limitations ? (
          <p className="flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
            <ShieldCheckIcon className="mt-0.5 size-3.5 shrink-0" />
            <span>{result.limitations}</span>
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
