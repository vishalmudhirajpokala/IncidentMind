import {
  ActivityIcon,
  ArrowUpRightIcon,
  CheckIcon,
  DatabaseIcon,
  GitBranchIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "lucide-react";

const investigationSteps = [
  "Signals analyzed",
  "Hindsight memory searched",
  "Historical pattern matched",
];

export function HeroProductPreview() {
  return (
    <div className="hero-product-frame overflow-hidden rounded-lg border border-border bg-card shadow-[0_28px_90px_-48px_rgba(10,54,157,0.48)]">
      <div className="flex h-12 items-center justify-between border-b border-border bg-muted/60 px-4 sm:px-5">
        <div className="flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ActivityIcon aria-hidden="true" className="size-4" />
          </span>
          <span className="text-xs font-medium text-foreground">IncidentMind / Command Center</span>
        </div>
        <span className="inline-flex items-center gap-2 text-[11px] text-muted-foreground">
          <span className="size-1.5 rounded-full bg-primary" />
          ILLUSTRATIVE INCIDENT
        </span>
      </div>

      <div className="grid xl:grid-cols-[0.94fr_1.06fr]">
        <section aria-labelledby="preview-incident-title" className="border-b border-border p-4 sm:p-6 xl:border-b-0 xl:border-r">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-muted-foreground">INC-184</p>
              <h2 id="preview-incident-title" className="mt-2 text-lg font-medium leading-snug text-foreground sm:text-xl">Checkout API degradation</h2>
              <p className="mt-1 text-sm text-muted-foreground">checkout-api · detected 4 min ago</p>
            </div>
            <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-[11px] font-medium uppercase text-primary">High</span>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="border-l-2 border-primary pl-3 py-1">
              <p className="text-xs text-muted-foreground">Error rate</p>
              <p className="mt-1 text-2xl font-medium tabular-nums">18.2<span className="text-base">%</span></p>
            </div>
            <div className="border-l-2 border-primary/50 pl-3 py-1">
              <p className="text-xs text-muted-foreground">DB connections</p>
              <p className="mt-1 text-2xl font-medium tabular-nums">96<span className="text-base">%</span></p>
            </div>
          </div>

          <div className="mt-6 rounded-md bg-muted/70 p-3.5">
            <div className="flex items-center gap-2 text-xs font-medium">
              <GitBranchIcon aria-hidden="true" className="size-4 text-primary" />
              Recent change
            </div>
            <p className="mt-2 text-sm text-muted-foreground">checkout-api v2.8.3 deployed shortly before the error spike.</p>
          </div>
        </section>

        <section aria-label="AI investigation status" className="p-4 sm:p-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <SparklesIcon aria-hidden="true" className="size-4 text-primary" />
              AI investigation
            </div>
            <span className="rounded-md bg-primary/10 px-2 py-1 text-[10px] font-medium text-primary">3 SPECIALIST ROLES</span>
          </div>

          <ol className="mt-4 space-y-3">
            {investigationSteps.map((step, index) => (
              <li key={step} className="flex items-center gap-3 text-sm" style={{ animationDelay: `${520 + index * 240}ms` }}>
                <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <CheckIcon aria-hidden="true" className="size-3" />
                </span>
                <span className="text-muted-foreground">{step}</span>
                {index === 2 ? <span className="ml-auto text-[10px] text-primary">MATCH</span> : null}
              </li>
            ))}
          </ol>

          <div className="mt-5 border-t border-border pt-4">
            <div className="flex items-center gap-2 text-xs font-medium uppercase text-muted-foreground">
              <DatabaseIcon aria-hidden="true" className="size-4 text-primary" />
              Hindsight memory
            </div>
            <p className="mt-2 text-sm">2 relevant experiences</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">Previous checkout incidents point to connection-pool exhaustion after deployment.</p>
          </div>
        </section>
      </div>

      <div className="flex flex-col gap-3 border-t border-primary/20 bg-primary/[0.045] p-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheckIcon aria-hidden="true" className="size-4" />
          </span>
          <div>
            <p className="text-[10px] font-medium uppercase text-primary">Recommendation · approval required</p>
            <p className="mt-1 text-sm font-medium">Rollback checkout-api to v2.8.2</p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1 self-start text-xs text-muted-foreground sm:self-auto">
          Review evidence <ArrowUpRightIcon aria-hidden="true" className="size-3.5" />
        </span>
      </div>
    </div>
  );
}
