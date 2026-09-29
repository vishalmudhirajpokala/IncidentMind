/**
 * Types mirroring the FastAPI response schemas exactly.
 *
 * These are hand-written rather than generated so that a mismatch between the
 * UI and the API is a type error at build time instead of a blank panel at
 * runtime. Field names and optionality follow `backend/app/schemas/`.
 */

export type ProviderMode = "live" | "demo" | "unavailable";

export type Severity = "low" | "medium" | "high" | "critical";

export type IncidentStatus = "active" | "investigating" | "mitigated" | "resolved";

export interface ProviderStatus {
  name: string;
  mode: ProviderMode;
  available: boolean;
  detail?: string | null;
  latency_ms?: number | null;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  env: string;
  demo_mode: boolean;
  database: ProviderStatus;
  memory: ProviderStatus;
  llm: ProviderStatus;
}

export interface Incident {
  id: string;
  title: string;
  service: string;
  severity: Severity;
  status: IncidentStatus;
  description?: string | null;
  signals: string[];
  metrics: Record<string, unknown>;
  deployment_version?: string | null;
  recent_change?: string | null;
  started_at?: string | null;
  detected_at?: string | null;
  resolved_at?: string | null;
  resolution_time_seconds?: number | null;
  root_cause?: string | null;
  action_taken?: string | null;
  failed_action?: string | null;
  outcome?: string | null;
  lesson?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MemoryEvidence {
  memory_id: string;
  source_incident_id?: string | null;
  historical_title?: string | null;
  historical_service?: string | null;
  historical_symptoms?: string | null;
  historical_root_cause?: string | null;
  historical_action?: string | null;
  historical_outcome?: string | null;
  historical_lesson?: string | null;
  why_relevant: string;
  matched_on: string[];
  rank: number;
  /** Always computed locally; `relevance_method` names the method. */
  relevance?: number | null;
  relevance_method?: string | null;
  provider: string;
  text?: string | null;
}

export interface Hypothesis {
  cause: string;
  confidence: number;
  evidence: string[];
}

export interface RecommendedAction {
  action: string;
  reason: string;
  risk: "low" | "medium" | "high";
  action_type: string;
  simulated: boolean;
  requires_approval: boolean;
}

export interface InvestigationResult {
  incident: Record<string, unknown>;
  mode: "memory_on" | "memory_off";
  summary: string;
  reasoning_summary: string;
  hypotheses: Hypothesis[];
  investigation_steps: string[];
  recommended_action?: RecommendedAction | null;
  confidence: number;
  memory_enabled: boolean;
  memory_count: number;
  memory_evidence: MemoryEvidence[];
  memory_source: string;
  memory_status: string;
  memory_query?: string | null;
  memory_detail?: string | null;
  memory_provider?: ProviderStatus | null;
  llm_provider?: ProviderStatus | null;
  limitations?: string | null;
  requires_human_approval: boolean;
  request_id: string;
  duration_ms: number;
}

export interface TelemetryPoint {
  metric: string;
  before: number;
  after: number;
  unit: string;
}

export interface SimulatedActionResult {
  incident_id: string;
  action: string;
  action_type: string;
  simulated: boolean;
  approved_by?: string | null;
  success: boolean;
  message: string;
  duration_seconds: number;
  telemetry: TelemetryPoint[];
  notes: string;
}

export interface ResolveResponse {
  incident_id: string;
  status: string;
  outcome: string;
  resolution_time_seconds?: number | null;
  retained: boolean;
  retain_status?: string | null;
  memory_event_id?: string | null;
}

export interface RetainResponse {
  incident_id: string;
  success: boolean;
  memory_event_id?: string | null;
  provider: string;
  external_retained: boolean;
  status: "retained" | "retained_locally" | "failed";
  detail?: string | null;
  external_ids: string[];
}

export interface MemoryRecallResponse {
  query: string;
  memories: MemoryEvidence[];
  count: number;
  source: string;
  status: string;
  detail?: string | null;
}

export interface MemoryEvent {  id: string;
  incident_id?: string | null;
  event_type: string;
  title?: string | null;
  symptoms?: string | null;
  content?: string | null;
  provider?: string | null;
  external_retained: boolean;
  external_ids: string[];
  retained_at?: string | null;
  event_metadata: Record<string, unknown>;
}

export interface MetricsOverview {
  incidents_total: number;
  incidents_active: number;
  incidents_resolved: number;
  by_severity: Record<string, number>;
  by_service: Record<string, number>;
  investigations_total: number;
  investigations_memory_on: number;
  investigations_memory_off: number;
  memory_events_total: number;
  memory_events_external: number;
  memory_events_local_only: number;
  average_confidence_memory_on?: number | null;
  average_confidence_memory_off?: number | null;
  average_resolution_time_seconds?: number | null;
  incidents_with_measured_resolution: number;
  providers: Record<string, ProviderStatus>;
}

export interface InvestigationRun {
  id: string;
  incident_id: string;
  mode: "memory_on" | "memory_off";
  summary: string;
  confidence: number;
  recommended_action?: string | null;
  memory_count: number;
  memory_source: string;
  llm_provider?: string | null;
  created_at?: string | null;
}

export interface IncidentHistory {
  incident_id: string;
  investigations: InvestigationRun[];
}

export interface DemoScenario {
  id: string;
  title: string;
  narrative: string;
  incident_a: Record<string, unknown>;
  incident_b: Record<string, unknown>;
  expected: string[];
}

export interface DemoRunStep {
  step: number;
  title: string;
  [key: string]: unknown;
}

export interface DemoRunResponse {
  scenario: DemoScenario;
  steps: DemoRunStep[];
  learning_proven: boolean;
  summary: string;
}

export interface DemoStatus {
  demo_mode: boolean;
  [key: string]: unknown;
}
