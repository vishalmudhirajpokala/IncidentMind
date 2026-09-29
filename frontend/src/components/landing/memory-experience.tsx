import {
  ActivityIcon,
  ArrowRightIcon,
  BrainCircuitIcon,
  CheckIcon,
  DatabaseIcon,
  RotateCcwIcon,
  SearchIcon,
  ShieldCheckIcon,
} from "lucide-react";

const loop = [
  { label: "Incident", icon: ActivityIcon },
  { label: "Investigate", icon: SearchIcon },
  { label: "Resolve", icon: CheckIcon },
  { label: "Retain experience", icon: DatabaseIcon },
  { label: "Hindsight", icon: BrainCircuitIcon },
  { label: "Future incident", icon: ActivityIcon },
  { label: "Recall", icon: RotateCcwIcon },
  { label: "Informed decision", icon: ShieldCheckIcon },
];

const practices = [
  {
    label: "RETAIN",
    title: "Capture the experience.",
    description: "Keep what happened, what was tried, what worked, what failed, and what the team learned.",
    icon: DatabaseIcon,
  },
  {
    label: "RECALL",
    title: "Find relevant experience.",
    description: "Retrieve prior incidents that resemble the current operational pattern.",
    icon: SearchIcon,
  },
  {
    label: "REFLECT",
    title: "Synthesize experience.",
    description: "Reason across accumulated memory when broader historical context is useful.",
    icon: BrainCircuitIcon,
  },
];

export function MemoryExperience() {
  return (
    <div className="space-y-14">
      <div className="rounded-lg border border-border bg-card px-4 py-6 sm:px-7">
        <div className="mb-6 flex items-center justify-between gap-4">
          <p className="text-xs font-medium uppercase text-primary">The Hindsight memory loop</p>
          <span className="hidden items-center gap-2 text-xs text-muted-foreground sm:inline-flex">
            <span className="size-1.5 rounded-full bg-primary" /> Experience carries forward
          </span>
        </div>
        <ol aria-label="Incident learning loop" className="grid grid-cols-2 gap-x-3 gap-y-5 sm:grid-cols-4 xl:grid-cols-8">
          {loop.map((step, index) => {
            const Icon = step.icon;
            return (
              <li key={step.label} className="memory-loop-step relative flex min-w-0 flex-col items-start gap-3" style={{ animationDelay: `${index * 90}ms` }}>
                <span className="flex size-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon aria-hidden="true" className="size-4" />
                </span>
                <span className="text-xs font-medium leading-snug">{step.label}</span>
                {index < loop.length - 1 ? (
                  <ArrowRightIcon aria-hidden="true" className="absolute right-1 top-3 hidden size-4 text-primary/50 xl:block" />
                ) : null}
              </li>
            );
          })}
        </ol>
      </div>

      <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
        <div>
          <p className="mb-3 text-xs font-medium uppercase text-primary">Experience that compounds</p>
          <h3 className="text-2xl font-medium leading-tight sm:text-3xl">A resolved incident becomes context for the next one.</h3>
          <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground">
            Hindsight stores and retrieves operational experience for investigations. It does not retrain the language model.
          </p>
          <div className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
            <DatabaseIcon aria-hidden="true" className="size-4 text-primary" />
            Example memory records · illustrative
          </div>
        </div>

        <div className="space-y-3">
          <MemoryRecord id="INC-172" title="Checkout API · post-deployment 503" cause="DB saturation" action="Rollback" outcome="Recovered" />
          <MemoryRecord id="INC-161" title="Checkout API · elevated connection wait" cause="Pool exhaustion" action="Rollback" outcome="Recovered" />
          <div className="flex flex-col gap-3 border border-primary/35 bg-primary/[0.045] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <SearchIcon aria-hidden="true" className="size-4" />
              </span>
              <div>
                <p className="text-xs font-medium uppercase text-primary">New incident · similar pattern detected</p>
                <p className="mt-1 text-sm">2 relevant experiences found</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground sm:max-w-48">Recommendation supported by prior outcomes</p>
          </div>
        </div>
      </div>

      <div className="grid gap-0 border-y border-border md:grid-cols-3 md:divide-x md:divide-border">
        {practices.map((practice) => {
          const Icon = practice.icon;
          return (
            <article key={practice.label} className="py-6 md:px-6 first:md:pl-0 last:md:pr-0">
              <div className="flex items-center gap-2 text-xs font-medium uppercase text-primary">
                <Icon aria-hidden="true" className="size-4" />
                {practice.label}
              </div>
              <h3 className="mt-3 text-lg font-medium">{practice.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{practice.description}</p>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function MemoryRecord({
  id,
  title,
  cause,
  action,
  outcome,
}: {
  id: string;
  title: string;
  cause: string;
  action: string;
  outcome: string;
}) {
  return (
    <article className="memory-record border border-border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] text-primary">{id}</p>
          <h4 className="mt-1 text-sm font-medium">{title}</h4>
        </div>
        <span className="rounded-md bg-muted px-2 py-1 text-[10px] font-medium uppercase text-muted-foreground">Prior experience</span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border pt-3 text-xs">
        <p><span className="block text-muted-foreground">Cause</span><span className="mt-1 block">{cause}</span></p>
        <p><span className="block text-muted-foreground">Action</span><span className="mt-1 block">{action}</span></p>
        <p><span className="block text-muted-foreground">Outcome</span><span className="mt-1 block">{outcome}</span></p>
      </div>
    </article>
  );
}
