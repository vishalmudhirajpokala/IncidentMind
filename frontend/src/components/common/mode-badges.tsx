import { ActivityIcon, BrainIcon, CpuIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { providerSummary } from "@/lib/format";
import type { HealthResponse, ProviderStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Provider chips in the header.
 *
 * These exist to make one claim impossible to miss: whether the memory and the
 * model are genuinely live or running as labelled fallbacks. A judge should
 * never have to guess which one they are looking at.
 */

export function ModeBadge({
  status,
  label,
  className,
}: {
  status: ProviderStatus | undefined;
  label: string;
  className?: string;
}) {
  const mode = providerSummary(status);
  const variant =
    mode === "live" ? "live" : mode === "demo" ? "demo" : "critical";

  return (
    <Badge variant={variant} className={className}>
      <span
        aria-hidden
        className={cn(
          "size-1.5 rounded-full",
          mode === "live" && "bg-status-live",
          mode === "demo" && "bg-status-demo",
          mode === "unavailable" && "bg-destructive",
        )}
      />
      {label}: {mode}
    </Badge>
  );
}

export function DemoModeBadge({
  demoMode,
  className,
}: {
  demoMode: boolean;
  className?: string;
}) {
  if (!demoMode) return null;
  return (
    <Badge variant="demo" className={className}>
      Demo mode
    </Badge>
  );
}

export function ProviderIndicators({
  health,
  className,
}: {
  health: HealthResponse | null;
  className?: string;
}) {
  if (!health) {
    return (
      <Badge variant="critical" className={className}>
        API unreachable
      </Badge>
    );
  }

  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      <Badge variant={health.database.available ? "ok" : "critical"}>
        <ActivityIcon />
        Database: {health.database.available ? "ok" : "down"}
      </Badge>
      <ModeBadge status={health.memory} label="Memory" />
      <ModeBadge status={health.llm} label="Model" />
    </div>
  );
}

/**
 * A single line stating the operational posture in words, for the dashboard
 * header. Colour alone is never the only carrier of this information.
 */
export function ModeSummary({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return "Cannot reach the IncidentMind API.";
  }
  const memory = providerSummary(health.memory);
  const llm = providerSummary(health.llm);
  const both = memory === "live" && llm === "live";

  if (both) {
    return "Hindsight memory and the Groq model are both live.";
  }
  if (memory === "live" || llm === "live") {
    return `Memory ${memory}, model ${llm}. The fallback provider handled the other.`;
  }
  return "Running on the local memory mirror and the deterministic analyst. Every result below is labelled demo, not live.";
}

export function MemoryIcon(props: React.ComponentProps<typeof BrainIcon>) {
  return <BrainIcon {...props} />;
}

export function ModelIcon(props: React.ComponentProps<typeof CpuIcon>) {
  return <CpuIcon {...props} />;
}
