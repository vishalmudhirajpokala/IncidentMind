"use client";

import { useEffect, useState } from "react";
import { ArrowUpRightIcon, CheckCircle2Icon, CircleDashedIcon } from "lucide-react";
import Link from "next/link";

import { HeroProductPreview } from "@/components/landing/hero-product-preview";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { MemoryEffect } from "@/components/dashboard/memory-effect";
import { RecentLearning } from "@/components/dashboard/recent-learning";
import { IncidentTable } from "@/components/incidents/incident-table";
import { api } from "@/lib/api-client";
import type { HealthResponse, Incident, MemoryEvent, MetricsOverview } from "@/lib/types";

interface PreviewData {
  checked: boolean;
  health: HealthResponse | null;
  incidents: Incident[] | null;
  metrics: MetricsOverview | null;
  memories: MemoryEvent[] | null;
}

const emptyData: PreviewData = {
  checked: false,
  health: null,
  incidents: null,
  metrics: null,
  memories: null,
};

function withTimeout<T>(request: Promise<T>, timeoutMs = 2500): Promise<T | null> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), timeoutMs);
    request.then(resolve, () => resolve(null)).finally(() => clearTimeout(timer));
  });
}

export function ProductShowcase() {
  const [data, setData] = useState(emptyData);

  useEffect(() => {
    let active = true;

    async function loadPreview() {
      const [health, incidents, metrics, memories] = await Promise.all([
        withTimeout(api.health()),
        withTimeout(api.listIncidents()),
        withTimeout(api.metrics()),
        withTimeout(api.recentMemories(3)),
      ]);

      if (!active) return;

      setData({
        checked: true,
        health,
        incidents,
        metrics,
        memories,
      });
    }

    void loadPreview();
    return () => {
      active = false;
    };
  }, []);

  const connected = data.health !== null;

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 border-b border-border pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase text-primary">Real product surface</p>
          <h3 className="mt-2 text-xl font-medium">The same console, opened from the landing page.</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground" role="status" aria-live="polite">
          {connected ? <CheckCircle2Icon aria-hidden="true" className="size-4 text-primary" /> : <CircleDashedIcon aria-hidden="true" className="size-4" />}
          {connected
            ? `API connected · ${data.health?.demo_mode ? "demo mode" : "operational mode"}`
            : data.checked
              ? "API unavailable · static product preview remains available"
              : "Checking for current product data"}
        </div>
      </div>

      <section aria-labelledby="showcase-command-center" className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/50 px-4 py-3 sm:px-5">
          <div>
            <p className="text-[10px] font-medium uppercase text-primary">01 / Command Center</p>
            <h4 id="showcase-command-center" className="mt-1 text-sm font-medium">Operational overview</h4>
          </div>
          <Link href="/dashboard" className="inline-flex min-h-9 items-center gap-1 text-xs font-medium text-primary hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
            Open Command Center <ArrowUpRightIcon aria-hidden="true" className="size-3.5" />
          </Link>
        </div>
        <div className="space-y-6 p-4 sm:p-5">
          {data.metrics ? (
            <div className="@container/main"><KpiCards metrics={data.metrics} /></div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {data.checked ? "Current metrics are not available from the API." : "Loading current metrics from the existing API."}
            </p>
          )}
          {data.incidents !== null ? (
            <div className="overflow-x-auto"><IncidentTable incidents={data.incidents} /></div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {data.checked ? "Current incident records are not available from the API." : "Loading current incident records."}
            </p>
          )}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section aria-labelledby="showcase-investigation" className="overflow-hidden rounded-lg border border-border bg-card">
          <div className="border-b border-border bg-muted/50 px-4 py-3 sm:px-5">
            <p className="text-[10px] font-medium uppercase text-primary">02 / Investigation</p>
            <h4 id="showcase-investigation" className="mt-1 text-sm font-medium">Signals, evidence, and recommendation</h4>
          </div>
          <div className="p-3 sm:p-4"><HeroProductPreview /></div>
        </section>

        <section aria-labelledby="showcase-learning" className="min-w-0 overflow-hidden rounded-lg border border-border bg-card">
          <div className="border-b border-border bg-muted/50 px-4 py-3 sm:px-5">
            <p className="text-[10px] font-medium uppercase text-primary">03 / Learning</p>
            <h4 id="showcase-learning" className="mt-1 text-sm font-medium">Outcomes become reusable experience</h4>
          </div>
          <div className="space-y-4 p-3 sm:p-4">
            {data.metrics ? <MemoryEffect metrics={data.metrics} /> : (
              <div className="border-l-2 border-primary bg-muted/50 p-4 text-sm text-muted-foreground">
                Memory comparisons appear here only when the API has measured investigations to report.
              </div>
            )}
            {data.memories !== null ? <RecentLearning events={data.memories} /> : (
              <p className="px-1 text-sm text-muted-foreground">
                {data.checked ? "Recent retained experience is not available from the API." : "Recent retained experience is loading from the existing API."}
              </p>
            )}
          </div>
        </section>
      </div>

      {!connected && data.checked ? (
        <p className="text-xs leading-relaxed text-muted-foreground">
          The live panels above are optional. The illustrated incident and architecture explain the product without implying an API request succeeded.
        </p>
      ) : null}
    </div>
  );
}
