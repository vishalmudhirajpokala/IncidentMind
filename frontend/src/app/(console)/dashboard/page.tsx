import { PageHeader } from "@/components/common/page-header";
import { ModeSummary } from "@/components/common/mode-badges";
import { ErrorState } from "@/components/common/states";
import { DemoRunner } from "@/components/dashboard/demo-runner";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { MemoryEffect } from "@/components/dashboard/memory-effect";
import { RecentLearning } from "@/components/dashboard/recent-learning";
import { IncidentTable } from "@/components/incidents/incident-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, backendLabel } from "@/lib/api-server";
import { byNewest } from "@/lib/format";
import type { HealthResponse, Incident, MemoryEvent, MetricsOverview } from "@/lib/types";

export const dynamic = "force-dynamic";

interface DashboardData {
  health: HealthResponse | null;
  incidents: Incident[];
  metrics: MetricsOverview | null;
  learning: MemoryEvent[];
  offline: string | null;
}

async function load(): Promise<DashboardData> {
  const [health, incidents, metrics, learning] = await Promise.all([
    api.health().catch(() => null),
    api.listIncidents().catch(() => []),
    api.metrics().catch(() => null),
    api.recentMemories(5).catch(() => []),
  ]);

  const offline =
    health === null && metrics === null
      ? `Cannot reach the IncidentMind API at ${backendLabel}. Start the backend, then reload.`
      : null;

  return {
    health,
    incidents: [...incidents].sort(byNewest),
    metrics,
    learning,
    offline,
  };
}

export default async function DashboardPage() {
  const { health, incidents, metrics, learning, offline } = await load();

  return (
    <div className="space-y-8">
      <PageHeader
        title="IncidentMind"
        subtitle="Memory-first incident response"
        actions={<DemoRunner />}
      />

      <div className="space-y-3">
        <h2 className="text-xl tracking-tight">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          {health ? ModeSummary({ health }) : "Every investigation run is shown here."}
        </p>
      </div>

      {offline ? <ErrorState title="API unreachable" message={offline} /> : null}

      {metrics ? <KpiCards metrics={metrics} /> : null}

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.9fr]">
        {metrics ? <MemoryEffect metrics={metrics} /> : null}
        <RecentLearning events={learning} />
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle>Incidents</CardTitle>
          <span className="text-xs text-muted-foreground">{incidents.length} visible</span>
        </CardHeader>
        <CardContent>
          <IncidentTable incidents={incidents} />
        </CardContent>
      </Card>
    </div>
  );
}