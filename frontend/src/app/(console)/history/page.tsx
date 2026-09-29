import Link from "next/link";
import { formatRelative } from "@/lib/format";
import { api, backendLabel } from "@/lib/api-server";
import { PageHeader } from "@/components/common/page-header";
import { ModeSummary } from "@/components/common/mode-badges";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { HealthResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

interface Run {
  id: string;
  incident_id: string;
  mode: string;
  summary: string;
  confidence: number;
  recommended_action?: string | null;
  memory_count: number;
  memory_source: string;
  llm_provider?: string | null;
  created_at?: string | null;
}

async function load(): Promise<{
  health: HealthResponse | null;
  runs: Run[];
  offline: string | null;
}> {
  const [health, history] = await Promise.all([
    api.health().catch(() => null),
    api.demoHistory().catch(
      () => null,
    ) as Promise<{ investigations?: Run[] } | null>,
  ]);

  const runs = Array.isArray(history?.investigations) ? history.investigations : [];

  return {
    health,
    runs,
    offline:
      health === null
        ? `Cannot reach the IncidentMind API at ${backendLabel}. Start the backend, then reload.`
        : null,
  };
}

export default async function HistoryPage() {
  const { health, runs, offline } = await load();

  return (
    <div className="px-4 lg:px-6">
      <PageHeader
        title="Investigation history"
        subtitle={
          health
            ? ModeSummary({ health })
            : "Every investigation run recorded in this deployment."
        }
      />

      {offline ? <ErrorState title="API unreachable" message={offline} /> : null}

      <Card>
          <CardHeader className="flex-row items-center justify-between gap-2">
            <CardTitle>Runs</CardTitle>
            <Badge variant="muted">{runs.length} recorded</Badge>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <EmptyState
                title="No investigations recorded"
                message="Investigate an incident and it will be recorded here, with the mode it ran in, so memory-on and memory-off runs can be compared after the fact."
              />
            ) : (
              <div className="overflow-hidden rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Incident</TableHead>
                      <TableHead>Mode</TableHead>
                      <TableHead>Summary</TableHead>
                      <TableHead>Memory</TableHead>
                      <TableHead className="text-right">Confidence</TableHead>
                      <TableHead className="text-right">When</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {runs.map((run) => (
                      <TableRow key={run.id}>
                        <TableCell>
                          <Link
                            href={`/incidents/${run.incident_id}`}
                            className="font-mono text-[11px] font-medium hover:underline"
                          >
                            {run.incident_id}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <Badge variant={run.mode === "memory_on" ? "live" : "muted"}>
                            {run.mode === "memory_on" ? "Memory on" : "Memory off"}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-[32rem]">
                          <p className="line-clamp-1 text-xs">{run.summary}</p>
                          {run.recommended_action ? (
                            <p className="line-clamp-1 text-[11px] text-muted-foreground">
                              {run.recommended_action}
                            </p>
                          ) : null}
                        </TableCell>
                        <TableCell>
                          <span className="tabular text-xs">
                            {run.memory_count} · {run.memory_source}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <span className="tabular text-xs">
                            {(run.confidence * 100).toFixed(0)}%
                          </span>
                        </TableCell>
                        <TableCell className="whitespace-nowrap text-right text-xs text-muted-foreground">
                          {formatRelative(run.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
      </Card>
    </div>
  );
}
