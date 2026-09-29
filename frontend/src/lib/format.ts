/** Presentation helpers. Formatting only; no business rules live here. */

import type { Incident, MemoryEvent, ProviderStatus, Severity } from "./types";

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function severityLabel(severity: string): string {
  return SEVERITY_LABEL[severity as Severity] ?? severity;
}

export function statusLabel(status: string): string {
  switch (status) {
    case "active":
      return "Active";
    case "investigating":
      return "Investigating";
    case "mitigated":
      return "Mitigated";
    case "resolved":
      return "Resolved";
    default:
      return status;
  }
}

/** "4m 12s" / "1h 04m" / "820ms". Deliberately compact for dense tables. */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "—";
  if (seconds < 1) return "<1s";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  if (minutes < 60) return `${minutes}m ${String(rest).padStart(2, "0")}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${String(minutes % 60).padStart(2, "0")}m`;
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function formatAbsolute(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * The first line of a retained experience, for the Recent Learning list.
 * Falls back through progressively less specific fields rather than showing
 * an empty row.
 */
export function experienceHeadline(event: MemoryEvent): string {
  const meta = event.event_metadata ?? {};
  const lesson = typeof meta.lesson === "string" ? meta.lesson : null;
  const rootCause = typeof meta.root_cause === "string" ? meta.root_cause : null;
  const action = typeof meta.successful_action === "string" ? meta.successful_action : null;
  return lesson ?? rootCause ?? action ?? event.title ?? "Retained experience";
}

export function experienceOutcome(event: MemoryEvent): string | null {
  const meta = event.event_metadata ?? {};
  const outcome = typeof meta.outcome === "string" ? meta.outcome : null;
  return outcome ?? null;
}

export function experienceService(event: MemoryEvent): string | null {
  const meta = event.event_metadata ?? {};
  const service = typeof meta.service === "string" ? meta.service : null;
  return service ?? null;
}

export function experienceErrorRate(event: MemoryEvent): string | null {
  const meta = event.event_metadata ?? {};
  const metrics = (meta.metrics ?? {}) as Record<string, unknown>;
  const raw = metrics.error_rate ?? metrics.errorRate;
  return typeof raw === "number" ? `${raw.toFixed(1)}% error rate at failure` : null;
}

export function providerSummary(status: ProviderStatus | undefined): string {
  if (!status) return "unknown";
  if (status.mode === "live") return "live";
  if (status.mode === "demo") return "demo";
  return "unavailable";
}

/** Sorts newest first, tolerating missing timestamps. */
export function byNewest<T extends { created_at?: string | null; detected_at?: string | null }>(
  a: T,
  b: T,
): number {
  const left = new Date(a.created_at ?? a.detected_at ?? 0).getTime();
  const right = new Date(b.created_at ?? b.detected_at ?? 0).getTime();
  return right - left;
}

export const SEVERITY_RANK: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export function incidentTimestamp(incident: Incident): string | null {
  return incident.detected_at ?? incident.started_at ?? incident.created_at ?? null;
}

/**
 * Pulls a scalar out of an incident's free-form metrics bag for display.
 * The backend stores whatever the caller supplied, so every read is guarded.
 */
export function metric(
  incident: Incident,
  keys: readonly string[],
): { label: string; value: string } | null {
  for (const key of keys) {
    const raw = incident.metrics?.[key];
    if (typeof raw === "number" && Number.isFinite(raw)) {
      return { label: key.replace(/_/g, " "), value: formatMetricNumber(key, raw) };
    }
  }
  return null;
}

function formatMetricNumber(key: string, value: number): string {
  if (key.includes("latency") || key.includes("duration")) return `${value.toLocaleString()} ms`;
  if (value < 1) return value.toFixed(3);
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}
