"use client";

import { useState } from "react";
import {
  ActivityIcon,
  BrainCircuitIcon,
  CheckIcon,
  CircleGaugeIcon,
  GitCompareArrowsIcon,
  ListChecksIcon,
  NetworkIcon,
  ShieldCheckIcon,
} from "lucide-react";

const agents = [
  {
    name: "Triage",
    role: "TRIAGE AGENT",
    icon: CircleGaugeIcon,
    summary: "Sets severity, scope, and urgency.",
    detail: "Triage determines how urgent the incident is, which services are affected, and what needs attention first.",
  },
  {
    name: "Memory",
    role: "MEMORY AGENT",
    icon: BrainCircuitIcon,
    summary: "Recalls similar incidents and outcomes.",
    detail: "The Memory Agent uses Hindsight to retrieve relevant experiences, previous actions, outcomes, and lessons.",
  },
  {
    name: "Observability",
    role: "OBSERVABILITY AGENT",
    icon: ActivityIcon,
    summary: "Reads current signals and changes.",
    detail: "Observability organizes logs, metrics, error signals, deployment context, and dependency evidence.",
  },
  {
    name: "Root Cause",
    role: "ROOT-CAUSE AGENT",
    icon: GitCompareArrowsIcon,
    summary: "Compares evidence and hypotheses.",
    detail: "Root-cause analysis weighs current signals against historical evidence and competing explanations.",
  },
  {
    name: "Action Planner",
    role: "ACTION PLANNER",
    icon: ListChecksIcon,
    summary: "Builds an evidence-backed next step.",
    detail: "The planner presents an action, its evidence and risk, and whether human approval is required.",
  },
  {
    name: "Incident Commander",
    role: "INCIDENT COMMANDER",
    icon: NetworkIcon,
    summary: "Combines findings into one decision.",
    detail: "The commander synthesizes specialist findings into a single actionable recommendation for the operator.",
  },
];

export function AgentNetwork() {
  const [selectedName, setSelectedName] = useState("Incident Commander");
  const selected = agents.find((agent) => agent.name === selectedName);
  if (!selected) return null;
  const SelectedIcon = selected.icon;

  return (
    <div className="agent-network" aria-label="Interactive specialist agent workflow">
      <div className="mx-auto flex max-w-sm items-center justify-center gap-3 rounded-md border border-primary/30 bg-primary/[0.04] px-4 py-3 text-sm font-medium">
        <span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <ActivityIcon aria-hidden="true" className="size-4" />
        </span>
        Current incident
        <span className="ml-auto font-mono text-xs text-primary">INC-184</span>
      </div>

      <div aria-hidden="true" className="network-connector mx-auto h-8 w-px bg-primary/50" />
      <p className="mb-3 text-center text-[11px] font-medium uppercase text-muted-foreground">Parallel investigation roles</p>

      <div className="grid gap-3 md:grid-cols-3">
        {agents.slice(0, 3).map((agent, index) => (
          <AgentButton key={agent.name} agent={agent} index={index} selected={selected.name === agent.name} onSelect={() => setSelectedName(agent.name)} />
        ))}
      </div>

      <div aria-hidden="true" className="network-connector mx-auto h-8 w-px bg-primary/50" />
      <div className="mx-auto mb-3 flex max-w-2xl items-center justify-center gap-2 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-primary/30" />
        Findings converge
        <span className="h-px flex-1 bg-primary/30" />
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {agents.slice(3).map((agent, index) => (
          <AgentButton key={agent.name} agent={agent} index={index + 3} selected={selected.name === agent.name} onSelect={() => setSelectedName(agent.name)} />
        ))}
      </div>

      <div aria-hidden="true" className="network-connector mx-auto h-8 w-px bg-primary/50" />
      <div className="mx-auto flex max-w-sm items-center justify-center gap-3 rounded-md border border-border bg-card px-4 py-3 text-sm">
        <ShieldCheckIcon aria-hidden="true" className="size-4 text-primary" />
        Human approval
        <span className="ml-auto text-xs text-muted-foreground">when required</span>
      </div>

      <div className="mt-5 flex min-h-16 items-start gap-3 border-l-2 border-primary pl-4" aria-live="polite">
        <SelectedIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" />
        <div>
          <p className="text-xs font-medium uppercase text-primary">{selected.role}</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{selected.detail}</p>
        </div>
        <CheckIcon aria-hidden="true" className="ml-auto mt-0.5 size-4 shrink-0 text-primary" />
      </div>
    </div>
  );
}

function AgentButton({
  agent,
  index,
  selected,
  onSelect,
}: {
  agent: (typeof agents)[number];
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const Icon = agent.icon;

  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      className={`agent-node group min-h-28 border p-4 text-left transition-[background-color,border-color,transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${selected ? "border-primary/50 bg-primary/[0.055]" : "border-border bg-card"}`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <span className={`mb-3 flex size-8 items-center justify-center rounded-md ${selected ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary"}`}>
        <Icon aria-hidden="true" className="size-4" />
      </span>
      <span className="block text-[10px] font-medium uppercase text-muted-foreground">{agent.role}</span>
      <span className="mt-1 block text-sm font-medium">{agent.name}</span>
      <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">{agent.summary}</span>
    </button>
  );
}
