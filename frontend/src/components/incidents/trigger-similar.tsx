"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRightIcon } from "lucide-react";

import { BusyLabel, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { api, ApiError } from "@/lib/api-client";
import { nextTemplate, nextVersion, takeNextTemplateId, templateIndexById } from "@/lib/similar-incidents";
import type { Incident } from "@/lib/types";

/**
 * Creates a new incident on the same service, worded differently, and opens it.
 *
 * This exists purely so the effect of a just-retained experience can be seen
 * immediately instead of being described. The wording comes from a fixed set of
 * simulated phrasings and the panel says so, so it is never mistaken for a real
 * alert arriving from production.
 */
export function TriggerSimilarDialog({
  sourceIncidentId,
  source,
  onClose,
}: {
  sourceIncidentId: string;
  source?: Incident | null;
  onClose: () => void;
}) {
  const router = useRouter();
  // Starts on the phrasing after the last one used, so two triggers in a row
  // cannot produce the same text. Read in a lazy initialiser because this is
  // client-only: touching `sessionStorage` during render would break SSR.
  const [index, setIndex] = React.useState(() => templateIndexById(takeNextTemplateId()));
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const template = nextTemplate(index);
  const service = source?.service ?? "checkout-api";
  const version = nextVersion(source?.deployment_version);

  async function create() {
    setBusy(true);
    setError(null);
    try {
      const created = await api.createIncident({
        title: template.title,
        service,
        severity: "high",
        status: "active",
        description: template.description,
        signals: template.signals,
        metrics: {},
        deployment_version: version,
        recent_change: `release ${version} was promoted shortly before the first report`,
      });
      onClose();
      router.push(`/incidents/${created.id}`);
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "The similar incident could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => (open ? undefined : onClose())}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Trigger a similar incident</DialogTitle>
          <DialogDescription>
            Creates a new incident on <span className="font-medium text-foreground">{service}</span>{" "}
            describing the same operational failure in different words, then opens it for
            investigation.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2.5 rounded-md border bg-muted/40 p-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant="outline">{service}</Badge>
            <Badge variant="outline">{version}</Badge>
            <Badge variant="demo">Simulated input</Badge>
          </div>
          <p className="text-sm font-medium">{template.title}</p>
          <p className="text-xs leading-relaxed text-muted-foreground">
            {template.description}
          </p>
          <ul className="space-y-0.5 pt-1">
            {template.signals.map((signal, i) => (
              <li key={i} className="flex gap-1.5 text-[11px] text-muted-foreground">
                <span aria-hidden className="mt-1.5 size-1 shrink-0 rounded-full bg-muted-foreground/60" />
                {signal}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-[11px] leading-relaxed text-muted-foreground">
          This text is a fixed demonstration phrasing, not telemetry from a real system. It
          deliberately avoids the vocabulary of {sourceIncidentId} so that retrieval has to
          match on the failure shape rather than on shared keywords.
        </p>

        {error ? <ErrorState message={error} /> : null}

        <DialogFooter className="sm:justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIndex((i) => i + 1)}
            disabled={busy}
          >
            Use a different phrasing
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button onClick={create} disabled={busy}>
              {busy ? (
                <BusyLabel>Creating…</BusyLabel>
              ) : (
                <>
                  Create and investigate<ArrowRightIcon />
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
