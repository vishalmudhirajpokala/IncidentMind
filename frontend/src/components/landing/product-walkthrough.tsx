import {
  ActivityIcon,
  ArrowDownIcon,
  BrainCircuitIcon,
  CheckIcon,
  DatabaseIcon,
  GitCompareArrowsIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "lucide-react";

const steps = [
  {
    number: "01",
    title: "Incident detected",
    description: "503 spike · database saturation · recent deployment",
    icon: ActivityIcon,
  },
  {
    number: "02",
    title: "Specialists investigate",
    description: "Triage, Memory, and Observability gather focused findings.",
    icon: SparklesIcon,
  },
  {
    number: "03",
    title: "Hindsight recalls experience",
    description: "Relevant prior incidents and their outcomes enter the evidence set.",
    icon: BrainCircuitIcon,
  },
  {
    number: "04",
    title: "Findings are synthesized",
    description: "Current signals and historical evidence support a likely cause.",
    icon: GitCompareArrowsIcon,
  },
  {
    number: "05",
    title: "A recommendation is prepared",
    description: "Rollback checkout-api to v2.8.2 · human approval required.",
    icon: ShieldCheckIcon,
  },
  {
    number: "06",
    title: "Outcome is observed",
    description: "18.2% → 2.1% error rate · SIMULATED example only.",
    icon: CheckIcon,
    simulated: true,
  },
  {
    number: "07",
    title: "Experience is retained",
    description: "The recorded outcome becomes retrievable context for a future investigation.",
    icon: DatabaseIcon,
  },
];

export function ProductWalkthrough() {
  return (
    <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
      <div className="lg:sticky lg:top-28 lg:self-start">
        <p className="mb-3 text-xs font-medium uppercase text-primary">A repeatable learning loop</p>
        <h2 className="text-3xl font-medium leading-tight sm:text-4xl">From alert to learned experience.</h2>
        <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
          Investigation produces a decision. Resolution records what happened. Hindsight makes the lesson available when a similar incident returns.
        </p>
        <div className="mt-8 flex items-center gap-3 border-l-2 border-primary pl-4">
          <span className="flex size-8 items-center justify-center rounded-md bg-primary/10 text-primary">
            <ArrowDownIcon aria-hidden="true" className="size-4" />
          </span>
          <span className="text-sm text-muted-foreground">The final step feeds the next investigation.</span>
        </div>
      </div>

      <ol className="walkthrough-list">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <li key={step.number} className="walkthrough-step relative grid grid-cols-[2.75rem_minmax(0,1fr)] gap-4 pb-8 last:pb-0" style={{ animationDelay: `${index * 100}ms` }}>
              {index < steps.length - 1 ? <span aria-hidden="true" className="absolute bottom-0 left-[1.32rem] top-11 w-px bg-border" /> : null}
              <span className="relative z-10 flex size-11 items-center justify-center rounded-md border border-primary/25 bg-background text-primary">
                <Icon aria-hidden="true" className="size-4" />
              </span>
              <div className="min-w-0 border-b border-border pb-6 last:border-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] text-primary">{step.number}</span>
                  <h3 className="text-sm font-medium">{step.title}</h3>
                  {step.simulated ? <span className="rounded-sm border border-primary/30 px-1.5 py-0.5 text-[9px] font-medium uppercase text-primary">Simulated</span> : null}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
