import Link from "next/link";
import {
  ActivityIcon,
  ArrowDownIcon,
  ArrowRightIcon,
  ArrowUpRightIcon,
  DatabaseIcon,
  FileTextIcon,
  GaugeIcon,
  GitBranchIcon,
  Layers3Icon,
  ScrollTextIcon,
  ServerIcon,
  ShieldCheckIcon,
  WaypointsIcon,
} from "lucide-react";

import { AgentNetwork } from "@/components/landing/agent-network";
import { HeroProductPreview } from "@/components/landing/hero-product-preview";
import { LandingNav } from "@/components/landing/landing-nav";
import { MemoryExperience } from "@/components/landing/memory-experience";
import { ProductShowcase } from "@/components/landing/product-showcase";
import { ProductWalkthrough } from "@/components/landing/product-walkthrough";
import { ScrollReveal } from "@/components/landing/scroll-reveal";

const sources = [
  { label: "Logs", icon: ScrollTextIcon },
  { label: "Metrics", icon: GaugeIcon },
  { label: "Deployments", icon: GitBranchIcon },
  { label: "Incident reports", icon: FileTextIcon },
  { label: "Engineer notes", icon: Layers3Icon },
];

const coldStart = [
  "Current incident",
  "Generic investigation",
  "Resolution",
  "Conversation ends",
  "Next incident starts cold",
];

const remembered = [
  "Current incident",
  "AI investigation",
  "Historical experience recalled",
  "Evidence-backed decision",
  "Outcome retained",
  "Future response starts informed",
];

const architectureAgents = ["Triage", "Memory", "Observability", "Root Cause", "Action Planner"];
const technologies = ["Next.js", "TypeScript", "Tailwind CSS", "shadcn/ui", "FastAPI", "Hindsight", "Groq"];

const githubSearch = "https://github.com/search?q=IncidentMind&type=repositories";

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-background text-foreground">
      <LandingNav />

      <main>
        <section className="relative border-b border-border/70">
          <div className="pointer-events-none absolute inset-0 -z-0 overflow-hidden" aria-hidden="true">
            <div className="hero-grid absolute inset-0 opacity-70" />
            <div className="absolute -right-40 -top-48 size-[34rem] rounded-full bg-primary/[0.045] blur-3xl" />
          </div>
          <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 pb-16 pt-14 sm:px-6 sm:pb-20 sm:pt-20 lg:grid-cols-[0.78fr_1.22fr] lg:gap-14 lg:px-8 lg:pb-24 lg:pt-24">
            <div className="hero-copy">
              <p className="hero-enter inline-flex items-center gap-2 text-[11px] font-medium uppercase text-primary" style={{ animationDelay: "70ms" }}>
                <span className="size-1.5 rounded-full bg-primary" />
                AI incident response · powered by Hindsight
              </p>
              <h1 className="hero-enter mt-5 max-w-xl text-4xl font-medium leading-[1.08] sm:text-5xl lg:text-6xl" style={{ animationDelay: "150ms" }}>
                Incidents happen.
                <span className="mt-2 block text-primary">Experience should compound.</span>
              </h1>
              <p className="hero-enter mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg" style={{ animationDelay: "240ms" }}>
                IncidentMind brings AI agents, operational evidence, and persistent organizational memory together so every resolved incident makes the next response smarter.
              </p>
              <p className="hero-enter mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground" style={{ animationDelay: "300ms" }}>
                An AI incident-response command center where collaborative specialist agents turn each resolution into reusable team experience.
              </p>
              <div className="hero-enter mt-8 flex flex-col gap-3 sm:flex-row" style={{ animationDelay: "370ms" }}>
                <Link href="/dashboard" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                  Open Command Center
                  <ArrowUpRightIcon aria-hidden="true" className="size-4" />
                </Link>
                <a href="#memory" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-border bg-background/75 px-5 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                  See How It Learns
                  <ArrowDownIcon aria-hidden="true" className="size-4 text-primary" />
                </a>
              </div>
              <div className="hero-enter mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground" style={{ animationDelay: "430ms" }}>
                <span className="inline-flex items-center gap-2"><span className="size-1.5 rounded-full bg-primary" />Specialist agent roles</span>
                <span className="inline-flex items-center gap-2"><span className="size-1.5 rounded-full bg-primary/55" />Persistent operational memory</span>
                <span className="inline-flex items-center gap-2"><span className="size-1.5 rounded-full bg-primary/30" />Human-approved actions</span>
              </div>
            </div>

            <div className="hero-enter min-w-0" style={{ animationDelay: "300ms" }}>
              <HeroProductPreview />
            </div>
          </div>
        </section>

        <section id="problem" className="scroll-mt-20 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="01 / THE PROBLEM"
                title={<>Every incident teaches something.<br className="hidden sm:block" /> Most teams lose the lesson.</>}
                description="Operational context gets scattered. The next investigation starts by rebuilding what the team already learned."
              />
              <div className="mt-11 grid gap-0 border-y border-border md:grid-cols-3 md:divide-x md:divide-border">
                <ProblemItem number="01" title="Context gets scattered" description="Logs, metrics, deployments, runbooks, and incident notes live across disconnected systems." />
                <ProblemItem number="02" title="Engineers rediscover old answers" description="A new outage often means reconstructing knowledge someone already gained during a previous incident." />
                <ProblemItem number="03" title="Stateless AI starts cold" description="A model can reason about today's incident, but does not automatically accumulate the team's operational experience." />
              </div>

              <div className="mt-10 flex flex-col items-stretch gap-4 border border-border bg-muted/35 p-4 sm:p-5 lg:flex-row lg:items-center">
                <div className="flex flex-wrap gap-2 lg:flex-1">
                  {sources.map((source) => {
                    const Icon = source.icon;
                    return (
                      <span key={source.label} className="inline-flex items-center gap-2 border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
                        <Icon aria-hidden="true" className="size-3.5 text-primary" />{source.label}
                      </span>
                    );
                  })}
                </div>
                <ArrowRightIcon aria-hidden="true" className="hidden size-5 shrink-0 text-primary lg:block" />
                <div className="grid gap-2 sm:grid-cols-2 lg:w-[22rem]">
                  <span className="border border-border bg-background px-3 py-2.5 text-xs">Scattered context</span>
                  <span className="border border-primary/30 bg-primary/[0.055] px-3 py-2.5 text-xs text-primary">Slow investigation</span>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        <section className="border-y border-border bg-muted/35 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="02 / WHAT CHANGES"
                title="What changes when the system remembers?"
                description="A resolution can end a conversation, or become useful context for the next response."
              />
              <div className="mt-11 grid gap-5 lg:grid-cols-2">
                <FlowColumn title="Without Organizational Memory" intro="The incident is resolved. The learning stays with the people who were there." steps={coldStart} />
                <FlowColumn title="IncidentMind" intro="The outcome is retained and can be recalled when a similar incident appears." steps={remembered} emphasized />
              </div>
            </ScrollReveal>
          </div>
        </section>

        <section id="agents" className="scroll-mt-20 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="03 / COLLABORATIVE INVESTIGATION"
                title={<>One incident.<br className="sm:hidden" /> Multiple agents. One decision.</>}
                description="IncidentMind divides investigation into focused specialist roles that can work concurrently, then combines their findings into one actionable recommendation."
              />
              <div className="mt-12 border-y border-border py-8 sm:py-10">
                <AgentNetwork />
              </div>
              <p className="mt-4 text-center text-xs text-muted-foreground">Workflow visualization of the implemented investigation stages. It does not represent separate browser requests.</p>
            </ScrollReveal>
          </div>
        </section>

        <section id="memory" className="scroll-mt-20 border-y border-border bg-muted/35 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="04 / HINDSIGHT MEMORY"
                title="Your incident history becomes operational memory."
                description="Resolved incidents should not disappear when the alert closes. Hindsight turns experience into reusable memory for future investigations."
              />
              <div className="mt-12"><MemoryExperience /></div>
            </ScrollReveal>
          </div>
        </section>

        <section id="walkthrough" className="scroll-mt-20 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="05 / FROM ALERT TO LEARNING"
                title="A decision becomes experience."
                description="Follow the investigation from operational signals through approval, outcome, and memory retention."
                align="left"
              />
              <div className="mt-12"><ProductWalkthrough /></div>
            </ScrollReveal>
          </div>
        </section>

        <section id="product-preview" className="scroll-mt-20 border-y border-border bg-muted/35 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="06 / THE PRODUCT"
                title="An operational workspace, not a chatbot."
                description="Explore the command center, investigation evidence, and retained learning in the actual IncidentMind interface. Live panels use the existing API when available."
                align="left"
              />
              <div className="mt-12"><ProductShowcase /></div>
            </ScrollReveal>
          </div>
        </section>

        <section id="technology" className="scroll-mt-20 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <SectionHeading
                eyebrow="07 / TECHNICAL ARCHITECTURE"
                title="Built as an AI system, not a UI demo."
                description="A typed application layer connects incident workflows to specialist reasoning, persistent memory, and controlled actions."
                align="left"
              />

              <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_0.66fr]">
                <ArchitectureDiagram />
                <div className="flex flex-col justify-between gap-8 border-l-2 border-primary pl-6 sm:pl-8">
                  <div>
                    <p className="text-xs font-medium uppercase text-primary">System boundaries</p>
                    <ul className="mt-5 space-y-4 text-sm text-muted-foreground">
                      <li className="flex gap-3"><ShieldCheckIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" /><span>Safe simulated actions with human approval where required.</span></li>
                      <li className="flex gap-3"><FileTextIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" /><span>Structured investigation outputs preserve evidence and risk.</span></li>
                      <li className="flex gap-3"><DatabaseIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" /><span>Hindsight stores and recalls operational experience; it does not retrain the model.</span></li>
                      <li className="flex gap-3"><ServerIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" /><span>Incident records and resolutions remain in the application database.</span></li>
                      <li className="flex gap-3"><ActivityIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" /><span>Demo mode is identified honestly in the running application.</span></li>
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-primary">Technology</p>
                    <ul className="mt-4 flex flex-wrap gap-2" aria-label="Technology stack">
                      {technologies.map((technology) => <li key={technology} className="border border-border bg-background px-3 py-2 text-xs text-muted-foreground">{technology}</li>)}
                    </ul>
                  </div>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        <section className="border-y border-primary/20 bg-primary/[0.045] py-16 sm:py-20">
          <div className="mx-auto flex max-w-7xl flex-col gap-7 px-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
            <div>
              <p className="text-xs font-medium uppercase text-primary">IncidentMind</p>
              <h2 className="mt-3 max-w-3xl text-3xl font-medium leading-tight sm:text-4xl">Let every incident make the next one smarter.</h2>
              <p className="mt-3 text-sm text-muted-foreground">Investigate with experience, not from zero.</p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/dashboard" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                Open Command Center <ArrowUpRightIcon aria-hidden="true" className="size-4" />
              </Link>
              <a href={githubSearch} target="_blank" rel="noreferrer" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-border bg-background px-5 text-sm font-medium transition-colors hover:border-primary/40 hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                View GitHub <ArrowUpRightIcon aria-hidden="true" className="size-4" />
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
}: {
  eyebrow: string;
  title: React.ReactNode;
  description: string;
  align?: "center" | "left";
}) {
  const centered = align === "center";

  return (
    <div className={centered ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      <p className="text-xs font-medium uppercase text-primary">{eyebrow}</p>
      <h2 className="mt-3 text-3xl font-medium leading-tight sm:text-4xl">{title}</h2>
      <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">{description}</p>
    </div>
  );
}

function ProblemItem({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <article className="py-6 md:px-6 first:md:pl-0 last:md:pr-0">
      <p className="font-mono text-[11px] text-primary">{number}</p>
      <h3 className="mt-4 text-lg font-medium">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
    </article>
  );
}

function FlowColumn({
  title,
  intro,
  steps,
  emphasized = false,
}: {
  title: string;
  intro: string;
  steps: string[];
  emphasized?: boolean;
}) {
  return (
    <article className={`comparison-panel border p-5 sm:p-7 ${emphasized ? "border-primary/35 bg-primary/[0.035]" : "border-border bg-card"}`}>
      <p className="text-xs font-medium uppercase text-muted-foreground">{emphasized ? "With organizational memory" : "Without organizational memory"}</p>
      <h3 className="mt-2 text-xl font-medium">{title}</h3>
      <p className="mt-2 min-h-10 text-sm leading-relaxed text-muted-foreground">{intro}</p>
      <ol className="mt-6 space-y-0">
        {steps.map((step, index) => (
          <li key={step} className="comparison-step relative flex min-h-11 items-start gap-3 pb-3 text-sm" style={{ animationDelay: `${index * 140}ms` }}>
            <span className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full ${emphasized ? "bg-primary text-primary-foreground" : "border border-border bg-muted text-muted-foreground"}`}>
              {emphasized ? <span className="size-1.5 rounded-full bg-current" /> : <span className="size-1 rounded-full bg-current" />}
            </span>
            <span className={index === steps.length - 1 && emphasized ? "font-medium text-primary" : "text-foreground"}>{step}</span>
            {index < steps.length - 1 ? <span aria-hidden="true" className={`absolute bottom-0 left-[0.58rem] top-6 w-px ${emphasized ? "bg-primary/30" : "bg-border"}`} /> : null}
          </li>
        ))}
      </ol>
    </article>
  );
}

function ArchitectureDiagram() {
  return (
    <div className="rounded-lg border border-border bg-card p-4 sm:p-6">
      <ol className="mx-auto flex max-w-md flex-col items-stretch">
        <ArchitectureNode icon={Layers3Icon} label="Next.js" detail="Application interface" />
        <ArchitectureArrow />
        <ArchitectureNode icon={ServerIcon} label="FastAPI" detail="Typed API contracts" />
        <ArchitectureArrow />
        <ArchitectureNode icon={WaypointsIcon} label="Incident orchestrator" detail="Coordinates the investigation" primary />
        <ArchitectureArrow />
        <li className="border border-border bg-muted/45 p-4">
          <p className="text-center text-[10px] font-medium uppercase text-muted-foreground">Specialist investigation roles</p>
          <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {architectureAgents.map((agent) => <li key={agent} className="border border-border bg-background px-2 py-2 text-center text-xs">{agent}</li>)}
          </ul>
        </li>
        <ArchitectureArrow />
        <ArchitectureNode icon={ActivityIcon} label="Incident Commander" detail="Synthesizes findings into one recommendation" primary />
        <li className="grid gap-3 pt-3 sm:grid-cols-3">
          <div className="flex items-center justify-center gap-2 border border-primary/25 bg-primary/[0.04] p-3 text-xs"><DatabaseIcon aria-hidden="true" className="size-4 text-primary" />Hindsight memory</div>
          <div className="flex items-center justify-center gap-2 border border-border bg-muted/40 p-3 text-xs"><GitBranchIcon aria-hidden="true" className="size-4 text-primary" />Groq LLM</div>
          <div className="flex items-center justify-center gap-2 border border-border bg-muted/40 p-3 text-xs"><ServerIcon aria-hidden="true" className="size-4 text-primary" />Application DB</div>
        </li>
      </ol>
    </div>
  );
}

function ArchitectureNode({
  icon: Icon,
  label,
  detail,
  primary = false,
}: {
  icon: typeof Layers3Icon;
  label: string;
  detail: string;
  primary?: boolean;
}) {
  return (
    <li className={`flex items-center gap-3 border p-3 sm:p-3.5 ${primary ? "border-primary/30 bg-primary/[0.045]" : "border-border bg-background"}`}>
      <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary"><Icon aria-hidden="true" className="size-4" /></span>
      <div><p className="text-sm font-medium">{label}</p><p className="mt-0.5 text-xs text-muted-foreground">{detail}</p></div>
    </li>
  );
}

function ArchitectureArrow() {
  return <li aria-hidden="true" className="flex h-7 justify-center text-primary"><ArrowDownIcon className="size-4" /></li>;
}

function Footer() {
  return (
    <footer className="bg-background py-12 sm:py-14">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 border-b border-border pb-10 sm:grid-cols-2 lg:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="inline-flex items-center gap-2 text-base font-medium"><span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground"><ActivityIcon aria-hidden="true" className="size-4" /></span>IncidentMind</Link>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">Memory-first AI incident response.</p>
          </div>
          <FooterLinks title="Product" links={[["Command Center", "/dashboard"], ["Incidents", "/dashboard#incidents"], ["Memory", "#memory"], ["Agents", "#agents"]]} />
          <FooterLinks title="Technology" links={[["Hindsight", "#technology"], ["FastAPI", "#technology"], ["Next.js", "#technology"], ["Groq", "#technology"]]} />
          <FooterLinks title="Resources" links={[["Documentation", "#technology"], ["GitHub", githubSearch], ["Architecture", "#technology"]]} />
        </div>
        <div className="flex flex-col gap-3 pt-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>Built for the AI Agents That Learn Using Hindsight hackathon.</p>
          <p>IncidentMind · Memory-first incident response</p>
        </div>
      </div>
    </footer>
  );
}

function FooterLinks({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <h2 className="text-xs font-medium uppercase">{title}</h2>
      <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
        {links.map(([label, href]) => (
          <li key={label}>
            {href.startsWith("https://") ? (
              <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 transition-colors hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                {label}<ArrowUpRightIcon aria-hidden="true" className="size-3" />
              </a>
            ) : (
              <a href={href} className="transition-colors hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">{label}</a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
