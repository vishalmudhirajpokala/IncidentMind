import { Badge } from "@/components/ui/badge";
import { severityLabel, statusLabel } from "@/lib/format";
import type { IncidentStatus, Severity } from "@/lib/types";

const SEVERITY_VARIANT: Record<Severity, "critical" | "high" | "medium" | "low"> = {
  critical: "critical",
  high: "high",
  medium: "medium",
  low: "low",
};

export function SeverityBadge({ severity }: { severity: string }) {
  const key = (severity in SEVERITY_VARIANT ? severity : "low") as Severity;
  return <Badge variant={SEVERITY_VARIANT[key]}>{severityLabel(key)}</Badge>;
}

const STATUS_VARIANT: Record<IncidentStatus, "critical" | "demo" | "ok" | "muted"> = {
  active: "critical",
  investigating: "demo",
  mitigated: "ok",
  resolved: "muted",
};

export function StatusBadge({ status }: { status: string }) {
  const key = (status in STATUS_VARIANT ? status : "active") as IncidentStatus;
  return (
    <Badge variant={STATUS_VARIANT[key]} className="font-normal">
      {statusLabel(key)}
    </Badge>
  );
}
