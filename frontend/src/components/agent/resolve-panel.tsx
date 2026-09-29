"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CheckIcon, GraduationCapIcon, PlusIcon, XIcon } from "lucide-react";

import { BusyLabel, ErrorState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api-client";
import { formatDuration } from "@/lib/format";
import type { ResolveResponse, RetainResponse } from "@/lib/types";

/**
 * Resolve the incident and record what was learned.
 *
 * The form is prefilled from the agent's own output where it can be — the
 * recommended action becomes the action taken, the top hypothesis becomes the
 * root cause — because re-typing what the agent just produced is friction with
 * no benefit. Everything stays editable, since the human is the one accountable
 * for the record.
 */
export function ResolvePanel({
  incidentId,
  rootCause,
  actionTaken,
  failedAction,
  outcome,
  lesson,
  durationSeconds,
  onResolved,
}: {
  incidentId: string;
  rootCause?: string | null;
  actionTaken?: string | null;
  failedAction?: string | null;
  outcome?: string | null;
  lesson?: string | null;
  durationSeconds?: number | null;
  onResolved: (response: ResolveResponse) => void;
}) {
  const router = useRouter();
  const [form, setForm] = React.useState({
    root_cause: rootCause ?? "",
    action_taken: actionTaken ?? "",
    failed_action: failedAction ?? "",
    outcome: outcome || "resolved",
    lesson: lesson ?? "",
  });
  const [retain, setRetain] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const set = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const response = await api.resolve(incidentId, {
        root_cause: form.root_cause || null,
        action_taken: form.action_taken || null,
        failed_action: form.failed_action || null,
        outcome: form.outcome || "resolved",
        lesson: form.lesson || null,
        ...(durationSeconds ? { resolution_time_seconds: durationSeconds } : {}),
        retain,
      });
      onResolved(response);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The incident could not be resolved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle>Resolve and record the outcome</CardTitle>
        {durationSeconds ? (
          <Badge variant="muted">Took {formatDuration(durationSeconds)}</Badge>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Root cause" required>
            <Textarea
              value={form.root_cause}
              onChange={set("root_cause")}
              placeholder="What actually caused this?"
              className="min-h-16"
            />
          </Field>

          <Field label="Action taken" hint="The remedy that worked">
            <Textarea
              value={form.action_taken}
              onChange={set("action_taken")}
              placeholder="What did you do?"
              className="min-h-16"
            />
          </Field>

          <Field label="Failed action" hint="Optional — worth keeping">
            <Input
              value={form.failed_action}
              onChange={set("failed_action")}
              placeholder="What did you try that did not work?"
            />
          </Field>

          <Field label="Outcome">
            <Input
              value={form.outcome}
              onChange={set("outcome")}
              placeholder="What is the state now?"
            />
          </Field>

          <div className="sm:col-span-2">
            <Field label="Lesson" hint="What should the next engineer recognize or do earlier if this happens again?">
              <Textarea
                value={form.lesson}
                onChange={set("lesson")}
                placeholder="What should the next engineer recognize or do earlier if this happens again?"
                className="min-h-16"
              />
            </Field>
          </div>
        </div>

        <label className="flex items-start gap-2 rounded-md border bg-muted/40 p-2.5 text-xs">
          <input
            type="checkbox"
            checked={retain}
            onChange={(event) => setRetain(event.target.checked)}
            // A native checkbox centres its drawn box inside the element, so
            // sizing the element to 24px gives a comfortable touch target
            // without making the tick itself look large.
            className="mt-0 size-6 shrink-0 accent-foreground"
          />
          <span className="leading-relaxed">
            <span className="font-medium">Retain this experience to memory.</span> Writes the
            structured record so the next similar incident can start from it. Requires a root
            cause.
          </span>
        </label>

        {error ? <ErrorState message={error} /> : null}

        <Button onClick={submit} disabled={busy || form.root_cause.trim().length === 0}>
          {busy ? (
            <BusyLabel>Resolving…</BusyLabel>
          ) : (
            <>
              <CheckIcon />
              {retain ? "Resolve and retain" : "Resolve incident"}
            </>
          )}
        </Button>

        {form.root_cause.trim().length === 0 ? (
          <p className="text-[11px] text-muted-foreground">
            A root cause is required before this experience can be retained.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        {required ? <span className="ml-0.5 text-destructive">*</span> : null}
      </Label>
      {children}
      {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

/**
 * Confirmation plus the next move.
 *
 * "Trigger a similar incident" is the payoff: it creates a new incident on the
 * same service with different wording, so the retained experience can be shown
 * changing a recommendation immediately rather than being asserted to.
 */
export function LearningConfirmation({
  incidentId,
  response,
  onTriggerSimilar,
}: {
  incidentId: string;
  response: ResolveResponse;
  onTriggerSimilar: () => void;
}) {
  const router = useRouter();
  const [busy, setBusy] = React.useState(false);
  const [retain, setRetain] = React.useState<RetainResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const retained = response.retained;
  const current = retain;

  async function retainNow() {
    setBusy(true);
    setError(null);
    try {
      setRetain(await api.retain(incidentId));
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The experience could not be retained.");
    } finally {
      setBusy(false);
    }
  }

  const showRetained = retained || current?.success;

  return (
    <Card className="evidence-edge rounded-l-none">
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-1.5">
          <GraduationCapIcon className="size-3.5 text-muted-foreground" />
          What the agent learned
        </CardTitle>
        <Badge variant={response.status === "resolved" ? "ok" : "demo"}>
          Incident {response.status}
        </Badge>
      </CardHeader>

      <CardContent className="space-y-3">
        <SummaryFrom incidentId={incidentId} />

        {response.resolution_time_seconds ? (
          <p className="text-xs text-muted-foreground">
            Resolved in {formatDuration(response.resolution_time_seconds)}.
          </p>
        ) : null}

        {showRetained ? (
          <div className="rounded-r-md border-l-3 border-status-ok bg-status-ok/8 py-2.5 pl-3 pr-3">
            <div className="flex items-center gap-1.5">
              <CheckIcon className="size-3.5 text-status-ok" />
              <p className="text-xs font-medium">
                Experience added to organizational memory.
              </p>
            </div>
            <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
              {current?.status === "retained" ? (
                <>
                  Written to the external memory service
                  {current.external_ids.length > 0
                    ? ` (${current.external_ids.length} item${current.external_ids.length === 1 ? "" : "s"}).`
                    : "."}
                </>
              ) : (
                <>
                  Held in the local memory mirror. The external service was not written to
                  {current?.detail ? ` (${current.detail})` : ""}, so this experience is
                  retrievable here but is not yet in Hindsight.
                </>
              )}
            </p>
          </div>
        ) : response.retain_status === "failed" ? (
          <div className="rounded-r-md border-l-3 border-destructive bg-destructive/5 py-2.5 pl-3 pr-3">
            <div className="flex items-center gap-1.5">
              <XIcon className="size-3.5 text-destructive" />
              <p className="text-xs font-medium">The incident is resolved but was not retained.</p>
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              Resolution is not undone by a failed retain. Record a root cause, then retain it
              explicitly.
            </p>
          </div>
        ) : null}

        {error ? <ErrorState message={error} /> : null}

        <div className="flex flex-wrap items-center gap-2 border-t pt-3">
          {!showRetained ? (
            <Button size="sm" onClick={retainNow} disabled={busy}>
              {busy ? <BusyLabel>Retaining…</BusyLabel> : <><GraduationCapIcon />Retain experience to memory</>}
            </Button>
          ) : null}

          <Button
            size="sm"
            variant={showRetained ? "default" : "outline"}
            onClick={onTriggerSimilar}
          >
            <PlusIcon />
            Trigger a similar incident
          </Button>
        </div>

        <p className="text-[11px] leading-relaxed text-muted-foreground">
          This opens a new incident on the same service with different wording. Investigating it
          shows whether the experience just retained changes the recommendation.
        </p>
      </CardContent>
    </Card>
  );
}

function Summary({ label, value }: { label: string; value?: string }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-[11px] font-medium text-muted-foreground">{label}</dt>
      <dd className="text-xs leading-relaxed">{value ?? "Not recorded"}</dd>
    </div>
  );
}

/** Pulls the recorded fields back off the incident after resolution. */
function SummaryFrom({ incidentId }: { incidentId: string }) {
  const [incident, setIncident] = React.useState<{
    root_cause?: string | null;
    action_taken?: string | null;
    failed_action?: string | null;
    lesson?: string | null;
  } | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    api
      .getIncident(incidentId)
      .then((found) => {
        if (!cancelled) setIncident(found);
      })
      .catch(() => {
        /* the confirmation still stands without these fields */
      });
    return () => {
      cancelled = true;
    };
  }, [incidentId]);

  return (
    <div className="grid gap-2.5 sm:col-span-2 sm:grid-cols-2">
      <Summary label="Root cause" value={incident?.root_cause ?? undefined} />
      <Summary label="Successful action" value={incident?.action_taken ?? undefined} />
      <Summary label="Failed action" value={incident?.failed_action ?? undefined} />
      <Summary label="Lesson retained" value={incident?.lesson ?? undefined} />
    </div>
  );
}
