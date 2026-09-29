"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PlayIcon, RotateCcwIcon, CheckIcon, XIcon, ArrowRightIcon } from "lucide-react";

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
import type { DemoRunResponse, DemoRunStep } from "@/lib/types";

/**
 * Runs the deterministic learning-loop scenario on demand.
 *
 * This exists so a judge can produce the before/after in seconds without
 * having to know the scenario ids. The steps shown are the ones the backend
 * actually executed, not a scripted narrative.
 */
export function DemoRunner() {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [running, setRunning] = React.useState(false);
  const [resetting, setResetting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<DemoRunResponse | null>(null);

  async function run() {
    setRunning(true);
    setError(null);
    try {
      setResult(await api.demoRun());
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The demo could not be run.");
    } finally {
      setRunning(false);
    }
  }

  async function reset() {
    setResetting(true);
    setError(null);
    try {
      await api.demoReset();
      setResult(null);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The demo could not be reset.");
    } finally {
      setResetting(false);
    }
  }

  return (
    <>
      <Button size="sm" onClick={run} disabled={running || resetting}>
        {running ? <BusyLabel>Running the loop…</BusyLabel> : <><PlayIcon />Run learning loop</>}
      </Button>
      <Button variant="outline" size="sm" onClick={reset} disabled={running || resetting}>
        {resetting ? <BusyLabel>Resetting…</BusyLabel> : <><RotateCcwIcon />Reset demo</>}
      </Button>

      {error ? <ErrorState message={error} className="mt-2" /> : null}

      <Dialog open={open || result !== null} onOpenChange={(next) => (next ? setOpen(true) : setOpen(false))}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Learning loop: incident A then incident B</DialogTitle>
            <DialogDescription>
              Two incidents on the same service, worded differently. The second one is analyzed
              twice — once with memory withheld, once with it — so the effect of memory is
              visible rather than asserted.
            </DialogDescription>
          </DialogHeader>

          {result ? (
            <div className="space-y-3">
              <div
                className={
                  result.learning_proven
                    ? "evidence-edge rounded-r-md bg-status-live/8 py-2.5 pl-3 pr-3"
                    : "rounded-r-md border-l-3 border-destructive bg-destructive/5 py-2.5 pl-3 pr-3"
                }
              >
                <div className="flex items-center gap-2">
                  {result.learning_proven ? (
                    <CheckIcon className="size-4 text-status-live" />
                  ) : (
                    <XIcon className="size-4 text-destructive" />
                  )}
                  <p className="text-sm font-medium">
                    {result.learning_proven
                      ? "Learning loop closed"
                      : "Learning loop did not close"}
                  </p>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {result.summary}
                </p>
              </div>

              <ol className="space-y-1.5">
                {result.steps.map((step) => (
                  <DemoStepRow key={step.step} step={step} />
                ))}
              </ol>
            </div>
          ) : running ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Investigating, simulating, retaining and re-investigating…
            </p>
          ) : null}

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
            {result ? (
              <Button asChild>
                <Link href={`/incidents/${String(result.steps.at(-1)?.incident_id ?? "")}`}>
                  Open the second incident<ArrowRightIcon />
                </Link>
              </Button>
            ) : null}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function DemoStepRow({ step }: { step: DemoRunStep }) {
  const incidentId = typeof step.incident_id === "string" ? step.incident_id : null;
  const detail = stepDetail(step);

  return (
    <li className="flex items-start gap-2.5 rounded-md border px-2.5 py-2">
      <span className="tabular mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-muted text-[10px] font-semibold">
        {step.step}
      </span>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <p className="text-xs font-medium">{step.title}</p>
          {incidentId ? (
            <Link
              href={`/incidents/${incidentId}`}
              className="font-mono text-[11px] text-muted-foreground hover:underline"
            >
              {incidentId}
            </Link>
          ) : null}
          {typeof step.memory_count === "number" ? (
            <Badge variant={step.memory_count > 0 ? "live" : "muted"}>
              {step.memory_count} memor{step.memory_count === 1 ? "y" : "ies"}
            </Badge>
          ) : null}
        </div>
        {detail ? (
          <p className="text-xs leading-relaxed text-muted-foreground">{detail}</p>
        ) : null}
      </div>
    </li>
  );
}

/**
 * Picks the most informative field on a step. The steps are heterogeneous by
 * design (each one reports what that stage produced), so this is a lookup
 * rather than a fixed template.
 */
function stepDetail(step: DemoRunStep): string | null {
  const candidates = [
    step.recommended_action,
    step.summary,
    step.message,
    step.historical_incident_id
      ? `Recalled ${String(step.historical_incident_id)}${
          typeof step.historical_root_cause === "string" && step.historical_root_cause
            ? `: ${step.historical_root_cause}`
            : ""
        }`
      : null,
    step.limitations,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim().length > 0) return candidate;
  }
  return null;
}
