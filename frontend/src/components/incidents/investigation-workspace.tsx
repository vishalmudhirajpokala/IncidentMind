"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { BrainIcon, RefreshCwIcon, SearchIcon, SplitIcon } from "lucide-react";

import { BusyLabel, EmptyState, ErrorState } from "@/components/common/states";
import { ActionApproval, SimulatedOutcome } from "@/components/agent/action-approval";
import { HypothesisList, InvestigationProgress } from "@/components/agent/investigation-progress";
import { RecommendationCard } from "@/components/agent/recommendation-card";
import { LearningConfirmation, ResolvePanel } from "@/components/agent/resolve-panel";
import { MemoryPanel } from "@/components/memory/memory-panel";
import { TriggerSimilarDialog } from "@/components/incidents/trigger-similar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, ApiError } from "@/lib/api-client";
import type {
  Incident,
  InvestigationResult,
  ResolveResponse,
  SimulatedActionResult,
} from "@/lib/types";

/**
 * The investigation workspace.
 *
 * Owns every state transition in the loop: investigate (with or without
 * memory), approve, simulate, resolve, retain, and open a similar incident. The
 * investigation response is held locally rather than pushed through
 * `router.refresh()` so the memory panel, the recommendation and the confidence
 * reading always come from the same run and cannot disagree on screen.
 *
 * The memory-OFF path is a first-class control, not a debug switch: it runs the
 * same analyst on the same incident with history withheld, so the difference in
 * the recommendation is attributable to memory and nothing else.
 */
export function InvestigationWorkspace({ incident }: { incident: Incident }) {
  const router = useRouter();

  const [on, setOn] = React.useState<InvestigationResult | null>(null);
  const [off, setOff] = React.useState<InvestigationResult | null>(null);
  const [view, setView] = React.useState<"on" | "off">("on");

  const [investigating, setInvestigating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [rejected, setRejected] = React.useState(false);

  const [outcome, setOutcome] = React.useState<SimulatedActionResult | null>(null);
  const [resolution, setResolution] = React.useState<ResolveResponse | null>(null);
  const [triggering, setTriggering] = React.useState(false);

  const current = view === "on" ? on : off;
  const resolved = incident.status === "resolved" || resolution !== null;

  async function investigate(memoryEnabled: boolean) {
    setInvestigating(true);
    setError(null);
    setRejected(false);
    try {
      const result = await api.investigate(incident.id, memoryEnabled);
      if (memoryEnabled) {
        setOn(result);
        setView("on");
      } else {
        setOff(result);
        setView("off");
      }
      router.refresh();
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "The investigation could not be completed.",
      );
    } finally {
      setInvestigating(false);
    }
  }

  // Loading the page for an incident that has been investigated before should
  // show its findings rather than an empty panel, so a first automatic pass
  // runs memory-ON once on mount if nothing has been investigated in this
  // session.
  const bootstrapped = React.useRef(false);
  React.useEffect(() => {
    if (bootstrapped.current || resolved) return;
    bootstrapped.current = true;
    void investigate(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident.id]);

  function handleApproved(result: SimulatedActionResult) {
    setOutcome(result);
    router.refresh();
  }

  function handleRejected() {
    setRejected(true);
    setOutcome(null);
  }

  function handleResolved(result: ResolveResponse) {
    setResolution(result);
  }

  return (
    <div className="grid grid-cols-1 gap-5 @4xl/main:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-4">
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div className="flex flex-wrap items-center gap-2">
              {/*
                A resolved incident can still be re-investigated by hand.

                These were disabled once the incident closed, which left the
                "Not investigated in this session" panel below offering a button
                that could never be pressed, and re-opening a closed incident
                showed no investigation evidence at all even though the run is on
                record. Nothing downstream depends on the incident being open:
                approval is separately blocked while `resolved`, and the automatic
                pass on mount is still skipped for closed incidents so a
                recommendation is never silently rewritten.
              */}
              <Button
                size="sm"
                onClick={() => investigate(true)}
                disabled={investigating}
              >
                {investigating && view === "on" ? (
                  <BusyLabel>Investigating…</BusyLabel>
                ) : (
                  <>
                    <SearchIcon />
                    {on ? "Re-investigate with memory" : "Investigate with memory"}
                  </>
                )}
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={() => investigate(false)}
                disabled={investigating}
                title="Runs the same analyst on the same incident with historical experience withheld."
              >
                {investigating && view === "off" ? (
                  <BusyLabel>Investigating…</BusyLabel>
                ) : (
                  <>
                    <SplitIcon />
                    Compare without memory
                  </>
                )}
              </Button>

              {on && off ? (
                <Badge variant="live" className="ml-auto">
                  <BrainIcon />
                  Control comparison ready
                </Badge>
              ) : null}
            </div>

            {error ? (
              <ErrorState
                // Names the capability that failed. "Something went wrong" is
                // true and useless; the reader needs to know whether the agent
                // is down or the memory store is, because they look the same
                // from a generic banner but have different consequences.
                title="Agent analysis temporarily unavailable"
                message={error}
                onRetry={() => investigate(view === "on")}
              />
            ) : null}

            {rejected ? (
              <p className="rounded-r-md border-l-2 border-status-demo bg-status-demo/8 py-2 pl-2.5 text-xs leading-relaxed">
                Recommendation rejected by the on-call engineer. Nothing was executed. You can
                re-investigate or resolve the incident with a recorded root cause.
              </p>
            ) : null}

            {on && off ? <MemoryComparison on={on} off={off} /> : null}
          </CardContent>
        </Card>

        {current ? (
          <>
            {on && off ? (
              <Tabs
                value={view}
                onValueChange={(next: string) => setView(next as "on" | "off")}
              >
                <TabsList>
                  <TabsTrigger value="on">With memory</TabsTrigger>
                  <TabsTrigger value="off">Without memory</TabsTrigger>
                </TabsList>
                <TabsContent value="on" className="space-y-4">
                  <InvestigationStack result={on} />
                </TabsContent>
                <TabsContent value="off" className="space-y-4">
                  <InvestigationStack result={off} />
                </TabsContent>
              </Tabs>
            ) : (
              <InvestigationStack result={current} />
            )}
          </>
        ) : !investigating && !error ? (
          <EmptyState
            title="Not investigated in this session"
            message="Run an investigation to recall how this organisation has seen this failure before. The agent will search memory, form candidate causes and propose a reversible action for your approval."
            action={
              <Button onClick={() => investigate(true)}>
                <SearchIcon />
                Investigate with memory
              </Button>
            }
          />
        ) : null}

        {outcome ? <SimulatedOutcome outcome={outcome} /> : null}

        {/*
          The trigger dialog lives here, outside the resolved/unresolved split.

          It used to be rendered only inside the branch for an incident resolved
          in this session, so on an incident that was already closed when the
          page was opened the button set `triggering` and nothing appeared —
          a control that looked live and did nothing. Triggering a similar
          incident is equally meaningful for a previously-resolved incident
          (its experience is in memory, which is the whole point of the
          exercise), so the dialog is now mounted once for both paths.
        */}
        {triggering ? (
          <TriggerSimilarDialog
            sourceIncidentId={incident.id}
            source={incident}
            onClose={() => setTriggering(false)}
          />
        ) : null}

        {resolved ? (
          resolution ? (
            <LearningConfirmation
              incidentId={incident.id}
              response={resolution}
              onTriggerSimilar={() => setTriggering(true)}
            />
          ) : (
            <LearningConfirmation
              incidentId={incident.id}
              response={{
                incident_id: incident.id,
                status: incident.status,
                outcome: incident.outcome ?? "resolved",
                resolution_time_seconds: incident.resolution_time_seconds ?? null,
                retained: false,
                retain_status: null,
              }}
              onTriggerSimilar={() => setTriggering(true)}
            />
          )
        ) : outcome ? (
          /*
            Prefilled from `on`, the memory-grounded run, and from the approval
            response — not from `current`. `current` follows whichever side of
            the comparison is on screen, so switching to the without-memory run
            while the resolve form is open would silently rewrite the recorded
            cause and remedy with the control's. Only the ON run can ever be
            approved, so only the ON run describes what was done.
          */
          <ResolvePanel
            incidentId={incident.id}
            rootCause={on?.hypotheses[0]?.cause ?? incident.root_cause}
            actionTaken={outcome?.action ?? on?.recommended_action?.action ?? incident.action_taken}
            failedAction={incident.failed_action}
            outcome={incident.outcome}
            lesson={incident.lesson}
            durationSeconds={outcome?.duration_seconds ?? null}
            onResolved={handleResolved}
          />
        ) : on?.recommended_action ? (
          <ResolvePanel
            incidentId={incident.id}
            rootCause={on.hypotheses[0]?.cause ?? incident.root_cause}
            actionTaken={on.recommended_action.action}
            failedAction={incident.failed_action}
            outcome={incident.outcome}
            lesson={incident.lesson}
            durationSeconds={incident.resolution_time_seconds}
            onResolved={handleResolved}
          />
        ) : null}
      </div>

      <div className="space-y-4">
        <MemoryPanel
          evidence={current?.memory_evidence ?? []}
          provider={current?.memory_provider}
          status={current?.memory_status}
          detail={current?.memory_detail}
          query={current?.memory_query}
          loading={investigating}
          memoryEnabled={current ? current.memory_enabled : view === "on"}
          searched={current !== null}
        />

        {current?.recommended_action ? (
          <Card>
            <CardContent className="pt-4">
              <ActionApproval
                incidentId={incident.id}
                result={current}
                disabled={investigating || resolved}
                // The memory-OFF run is a control, not an alternative plan. Only
                // the memory-grounded recommendation may be approved.
                controlRun={view === "off"}
                onApproved={handleApproved}
                onRejected={handleRejected}
              />
            </CardContent>
          </Card>
        ) : null}

        {on && off ? (
          <Card>
            <CardContent className="space-y-2 pt-4">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Run history
              </p>
              <ul className="space-y-1 text-xs">
                <li className="flex items-baseline justify-between gap-2">
                  <span className="text-muted-foreground">With memory</span>
                  <span className="tabular font-medium">
                    {(on.confidence * 100).toFixed(0)}% · {on.memory_count} recalled
                  </span>
                </li>
                <li className="flex items-baseline justify-between gap-2">
                  <span className="text-muted-foreground">Without memory</span>
                  <span className="tabular font-medium">
                    {(off.confidence * 100).toFixed(0)}% · 0 recalled
                  </span>
                </li>
              </ul>
              <Button
                variant="ghost"
                size="sm"
                className="w-full"
                onClick={() => {
                  setView(view === "on" ? "off" : "on");
                }}
              >
                <RefreshCwIcon />
                Show the {view === "on" ? "without-memory" : "with-memory"} run
              </Button>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

function InvestigationStack({ result }: { result: InvestigationResult }) {
  return (
    <>
      <InvestigationProgress result={result} />
      <HypothesisList result={result} />
      <RecommendationCard result={result} />
    </>
  );
}

/**
 * Side-by-side of the two runs on the same incident.
 *
 * Only rendered once both runs exist. The delta is stated in the agent's own
 * words from the memory-ON reasoning summary, and the two recommendations are
 * printed in full, because the whole claim is that memory changed the answer.
 */
function MemoryComparison({
  on,
  off,
}: {
  on: InvestigationResult;
  off: InvestigationResult;
}) {
  const delta = on.confidence - off.confidence;

  return (
    <div className="rounded-r-md border-l-3 border-status-live bg-status-live/8 py-2.5 pl-3 pr-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-semibold">Memory changed the recommendation</p>
        <Badge variant={delta > 0 ? "live" : "muted"} className="tabular">
          {delta > 0 ? "Supportive" : "Unchanged"}
        </Badge>
      </div>

      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <div className="rounded-md border bg-card px-2.5 py-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            Without memory
          </p>
          <p className="mt-1 text-xs leading-relaxed">
            {off.recommended_action?.action ?? "No recommendation"}
          </p>
        </div>
        <div className="rounded-md border bg-card px-2.5 py-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            With memory
          </p>
          <p className="mt-1 text-xs leading-relaxed">
            {on.recommended_action?.action ?? "No recommendation"}
          </p>
        </div>
      </div>

      {on.reasoning_summary ? (
        <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
          {on.reasoning_summary}
        </p>
      ) : null}
    </div>
  );
}

/** Placeholder kept intentionally empty: see `SimilarIncidentTrigger` below. */

