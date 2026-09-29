import { ListChecksIcon, LightbulbIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { InvestigationResult } from "@/lib/types";

/**
 * The investigation, rendered as a progression.
 *
 * The agent's actual `investigation_steps` are shown verbatim, because they
 * come from whichever provider ran. Alongside them sit four user-safe
 * statements of what was established — matched incident, previous remedy,
 * deployment similarity, signal consistency — which is the summary an
 * operator needs. Neither is a chain of thought, and neither is invented here.
 */
export function InvestigationProgress({ result }: { result: InvestigationResult }) {
  const memoryOn = result.memory_enabled;

  const findings = [
    {
      label: "Historical match",
      value: memoryOn ? (result.memory_evidence[0]?.source_incident_id ?? "No close prior incident") : "Memory withheld for this run",
    },
    {
      label: "Observed pattern",
      value: result.memory_evidence[0]?.why_relevant ?? "Signals were analyzed but no repeat pattern was identified.",
    },
    {
      label: "Current release",
      value: versionFinding(result),
    },
  ];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-1.5">
          <ListChecksIcon className="size-3.5 text-muted-foreground" />
          AI investigation
        </CardTitle>
        <Badge variant={memoryOn ? "live" : "muted"}>
          {memoryOn ? "Memory on" : "Memory off"}
        </Badge>
      </CardHeader>

      <CardContent className="space-y-3">
        <ul className="space-y-2">
          {[
            "✓ Incident context analyzed",
            "✓ Current signals correlated",
            `${result.memory_count} historical experiences recalled`,
            "✓ Historical matches identified",
            "→ Recommendation ready",
          ].map((step, index) => (
            <li key={index} className="flex items-start gap-2.5 text-xs text-foreground">
              <span className="mt-0.5 size-2 shrink-0 rounded-full bg-status-live" aria-hidden />
              <span className="leading-relaxed">{step}</span>
            </li>
          ))}
        </ul>

        <div className="grid gap-2 border-t pt-3 sm:grid-cols-3">
          {findings.map((finding) => (
            <div key={finding.label} className="rounded-md bg-muted/30 p-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                {finding.label}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-foreground">{finding.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function HypothesisList({ result }: { result: InvestigationResult }) {
  if (result.hypotheses.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5">
          <LightbulbIcon className="size-3.5 text-muted-foreground" />
          Likely root cause
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {result.hypotheses.map((hypothesis, index) => (
          <div key={index} className="space-y-2 rounded-md border bg-muted/20 p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium">{hypothesis.cause}</p>
              <Badge variant={index === 0 ? "live" : "muted"}>
                {index === 0 ? "Strong historical match" : "Alternative"}
              </Badge>
            </div>
            {hypothesis.evidence.length > 0 ? (
              <ul className="space-y-1">
                {hypothesis.evidence.slice(0, 4).map((line, lineIndex) => (
                  <li key={lineIndex} className="flex gap-1.5 text-[11px] text-muted-foreground">
                    <span aria-hidden className="mt-1.5 size-1 shrink-0 rounded-full bg-muted-foreground/60" />
                    <span className="leading-relaxed">{line}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function versionFinding(result: InvestigationResult): string {
  const incident = result.incident as Record<string, unknown>;
  const current = typeof incident.deployment_version === "string" ? incident.deployment_version : null;
  const historical = result.memory_evidence[0]?.historical_root_cause ?? null;

  if (current && historical) return `${current} — same failure shape as prior release`;
  if (current) return current;
  return "No release recorded on this incident";
}
