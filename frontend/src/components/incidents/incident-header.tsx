import Link from "next/link";
import { ChevronLeftIcon } from "lucide-react";

import { SeverityBadge, StatusBadge } from "@/components/incidents/badges";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatAbsolute } from "@/lib/format";
import type { Incident } from "@/lib/types";

export function IncidentHeader({ incident }: { incident: Incident }) {
  return (
    <div className="space-y-3">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/dashboard">
          <ChevronLeftIcon />
          Command center
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-semibold text-muted-foreground">
              {incident.id}
            </span>
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
            <Badge variant="outline">{incident.service}</Badge>
          </div>
          <h1 className="max-w-[72ch] text-2xl leading-tight md:text-3xl">{incident.title}</h1>
          <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span>Started {formatAbsolute(incident.detected_at ?? incident.started_at)}</span>
            {incident.deployment_version ? (
              <span>Release {incident.deployment_version}</span>
            ) : null}
            {incident.resolved_at ? (
              <span>Resolved {formatAbsolute(incident.resolved_at)}</span>
            ) : null}
          </p>
        </div>
      </div>

      {incident.description ? (
        <p className="max-w-[72ch] text-sm leading-relaxed text-muted-foreground">
          {incident.description.length > 180
            ? `${incident.description.slice(0, 180).trim()}…`
            : incident.description}
        </p>
      ) : null}
    </div>
  );
}
