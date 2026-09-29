import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeftIcon } from "lucide-react";

import { ErrorState } from "@/components/common/states";
import { IncidentHeader } from "@/components/incidents/incident-header";
import { InvestigationWorkspace } from "@/components/incidents/investigation-workspace";
import { SignalsPanel } from "@/components/incidents/signals-panel";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-server";
import type { Incident } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function IncidentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const incidentResult = await api.getIncident(id).then(
    (value): [Incident | null, string | null] => [value, null],
    (cause): [Incident | null, string | null] => [
      null,
      cause instanceof Error ? cause.message : "The incident could not be loaded.",
    ],
  );

  const [incident, loadError] = incidentResult;

  // A genuinely unknown id is a 404; a backend outage is a rendered error. The
  // two must not look the same, or a broken API reads as a missing incident.
  if (!incident && loadError?.includes("not found")) notFound();

  return (
    <div className="mx-auto max-w-[1280px] px-4 py-4 md:px-6 lg:px-8">
      {!incident ? (
        <div className="space-y-4">
          <Button asChild variant="ghost" size="sm" className="-ml-2">
            <Link href="/dashboard">
              <ChevronLeftIcon />
              Command center
            </Link>
          </Button>
          <ErrorState
            title="Cannot load this incident"
            message={loadError ?? "Unknown error."}
          />
        </div>
      ) : (
        <>
          <IncidentHeader incident={incident} />
          <SignalsPanel incident={incident} />
          <InvestigationWorkspace incident={incident} />
        </>
      )}
    </div>
  );
}
