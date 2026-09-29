"use client";

import * as React from "react";
import { CheckIcon, PlayIcon, XIcon, UserCheckIcon } from "lucide-react";

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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api-client";
import type { InvestigationResult, SimulatedActionResult } from "@/lib/types";

/**
 * Human approval.
 *
 * The approve button is behind a confirmation that names the human, because
 * the backend requires `"approved": true` and records `approved_by`. Rejecting
 * is a first-class outcome here, not a dismissal: it records that a person saw
 * the recommendation and declined it, which is a real operational outcome.
 *
 * There is no "auto-approve" path anywhere in the UI.
 *
 * `controlRun` is for the memory-OFF comparison. That run exists to show what
 * memory contributed, and approving it would write a remedy the memory never
 * supported onto the incident — which is then simulated, recorded as the action
 * taken, and retained as the experience the next incident learns from. A
 * counterfactual is exactly the thing that must never become an experience, so
 * the control is read-only.
 */
export function ActionApproval({
  incidentId,
  result,
  disabled,
  controlRun = false,
  onApproved,
  onRejected,
}: {
  incidentId: string;
  result: InvestigationResult;
  disabled?: boolean;
  controlRun?: boolean;
  onApproved: (outcome: SimulatedActionResult) => void;
  onRejected: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [approver, setApprover] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // The dialog shows the action of whichever run is on screen. If that run
  // changes underneath an open dialog, the text on the confirm button would no
  // longer describe what gets approved, so it closes instead. Declared before
  // the early return below so the hook order stays stable.
  React.useEffect(() => {
    if (controlRun) setOpen(false);
  }, [controlRun]);

  const action = result.recommended_action;
  if (!action) return null;

  const blocked = Boolean(disabled) || controlRun;

  async function approve() {
    if (!action) return;
    setBusy(true);
    setError(null);
    try {
      const outcome = await api.simulateAction(incidentId, {
        action: action.action,
        // Strictly the JSON literal true: the backend rejects anything else
        // with 409, and this UI must never coerce a loose value into consent.
        approved: true,
        approved_by: approver.trim() || "on-call engineer",
      });
      setOpen(false);
      onApproved(outcome);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The action could not be simulated.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" onClick={() => setOpen(true)} disabled={blocked}>
          <UserCheckIcon />
          Approve simulated action
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={blocked}
          onClick={() => onRejected()}
        >
          <XIcon />
          Reject
        </Button>
        {controlRun ? (
          <span className="text-[11px] text-muted-foreground">
            This is the control run with memory withheld. Approval is off here — only the
            memory-grounded recommendation can be approved, otherwise the counterfactual
            would be recorded as the remedy.
          </span>
        ) : result.requires_human_approval ? (
          <span className="text-[11px] text-muted-foreground">
            Nothing executes without this approval.
          </span>
        ) : null}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve a simulated action</DialogTitle>
            <DialogDescription>
              This records your approval and runs a simulation. No production system is
              contacted and no command is executed.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 rounded-md border bg-muted/40 p-3">
            <p className="text-sm font-medium">{action.action}</p>
            <p className="text-xs text-muted-foreground">{action.reason}</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="approver">Approved by</Label>
            <Input
              id="approver"
              value={approver}
              onChange={(event) => setApprover(event.target.value)}
              placeholder="Your name or handle"
              autoComplete="off"
            />
            <p className="text-[11px] text-muted-foreground">
              Recorded on the incident. There is no auth in this MVP, so this is attribution
              only.
            </p>
          </div>

          {error ? <ErrorState message={error} /> : null}

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={busy}>
              Cancel
            </Button>
            <Button onClick={approve} disabled={busy}>
              {busy ? (
                <BusyLabel>Simulating…</BusyLabel>
              ) : (
                <>
                  <PlayIcon />
                  Approve and simulate
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * The simulated outcome.
 *
 * Before/after telemetry is the only place a delta is shown, and it comes
 * straight from the provider's `telemetry` array. Nothing is recomputed here.
 */
export function SimulatedOutcome({ outcome }: { outcome: SimulatedActionResult }) {
  return (
    <div className="rounded-r-md border-l-3 border-status-ok bg-status-ok/8 py-3 pl-3.5 pr-3">
      <div className="flex flex-wrap items-center gap-2">
        {outcome.success ? (
          <CheckIcon className="size-4 text-status-ok" />
        ) : (
          <XIcon className="size-4 text-status-demo" />
        )}
        <p className="text-sm font-medium">
          {outcome.success ? "Simulated action recovered the service" : "Simulated action did not fully recover the service"}
        </p>
        {outcome.approved_by ? (
          <span className="text-[11px] text-muted-foreground">approved by {outcome.approved_by}</span>
        ) : null}
      </div>

      <p className="mt-1 text-xs leading-relaxed">{outcome.message}</p>

      {outcome.telemetry.length > 0 ? (
        <dl className="mt-2.5 grid gap-2 sm:grid-cols-2">
          {outcome.telemetry.map((point) => (
            <div key={point.metric} className="rounded-md border bg-card px-2.5 py-2">
              <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {point.metric.replace(/_/g, " ")}
              </dt>
              <dd className="tabular mt-0.5 flex items-baseline gap-2 text-sm">
                <span className="text-muted-foreground line-through">
                  {point.before}
                  {point.unit === "percent" ? "%" : ""}
                </span>
                <span aria-hidden className="text-muted-foreground/50">
                  &rarr;
                </span>
                <span className="font-semibold text-status-ok">
                  {point.after}
                  {point.unit === "percent" ? "%" : ""}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      <p className="mt-2.5 text-[11px] text-muted-foreground">{outcome.notes}</p>
    </div>
  );
}
