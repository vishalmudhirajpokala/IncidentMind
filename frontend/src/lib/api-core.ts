/**
 * The HTTP layer.
 *
 * Two rules shape this file:
 *
 *  1. A failed API call must never produce a blank screen, so every failure is
 *     normalised into an `ApiError` carrying a message a human can act on. The
 *     backend's `detail` is passed through when it is already written for a
 *     human; raw bodies, stack traces and credentials never are.
 *  2. The backend base URL must not reach the browser, so the two environments
 *     bind the same endpoint set to different bases in `api-server` and
 *     `api-client`. This module is the only place that knows a URL.
 */

import type {
  DemoRunResponse,
  DemoScenario,
  DemoStatus,
  HealthResponse,
  Incident,
  IncidentHistory,
  InvestigationResult,
  MemoryEvent,
  MemoryRecallResponse,
  MetricsOverview,
  ResolveResponse,
  RetainResponse,
  SimulatedActionResult,
} from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  /** True when the request never reached the API at all. */
  readonly offline: boolean;

  constructor(message: string, status: number, detail: string, offline = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.offline = offline;
  }
}

type Json = Record<string, unknown>;

function friendly(status: number, rawDetail: unknown, offline: boolean): string {
  if (offline) {
    // No port here: this module is shared by the server and the browser, and
    // only the server knows which host the backend is actually on. The pages
    // add the real address, so the message never names the wrong port.
    return "Cannot reach the IncidentMind API.";
  }

  // The backend writes `detail` as a human sentence for 404 and 409, so it is
  // safe and better to pass it straight through.
  if (typeof rawDetail === "string" && rawDetail.length > 0) return rawDetail;

  // FastAPI validation errors arrive as a list of field objects.
  if (Array.isArray(rawDetail)) {
    const first = rawDetail[0] as Json | undefined;
    const field = typeof first?.loc === "object" ? (first.loc as unknown[]).at(-1) : undefined;
    return field
      ? `That value is not valid: ${String(field)}.`
      : "The request was not valid.";
  }

  if (status === 404) return "Not found.";
  if (status === 409) return "That action is not allowed right now.";
  if (status === 422) return "The request was not valid.";
  if (status >= 500) return "The IncidentMind API reported an internal error.";
  return "The request could not be completed.";
}

async function request<T>(
  base: string,
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const { json, ...rest } = init ?? {};
  const url = `${base}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...rest,
      // Incidents change on every action; nothing here is cacheable.
      cache: "no-store",
      headers: {
        ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
        ...rest.headers,
      },
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch (cause) {
    const reason = cause instanceof Error ? cause.message : "network error";
    throw new ApiError("Cannot reach the IncidentMind API.", 0, reason, true);
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let body: unknown = null;
  if (text.length > 0) {
    try {
      body = JSON.parse(text);
    } catch {
      // A non-JSON body from a 200 is still a failure to render, not a crash.
      if (response.ok) {
        throw new ApiError(
          "The API returned a response the UI could not read.",
          response.status,
          "unparseable body",
        );
      }
    }
  }

  if (!response.ok) {
    const detail = (body as Json | null)?.detail;
    throw new ApiError(
      friendly(response.status, detail, false),
      response.status,
      typeof detail === "string" ? detail : `HTTP ${response.status}`,
    );
  }

  return body as T;
}

export interface Endpoints {
  health: () => Promise<HealthResponse>;
  metrics: () => Promise<MetricsOverview>;

  listIncidents: (query?: string) => Promise<Incident[]>;
  getIncident: (id: string) => Promise<Incident>;
  createIncident: (payload: Json) => Promise<Incident>;
  incidentHistory: (id: string) => Promise<IncidentHistory>;

  investigate: (id: string, memoryEnabled: boolean) => Promise<InvestigationResult>;
  simulateAction: (id: string, payload: Json) => Promise<SimulatedActionResult>;
  resolve: (id: string, payload: Json) => Promise<ResolveResponse>;
  retain: (id: string) => Promise<RetainResponse>;

  recentMemories: (limit?: number) => Promise<MemoryEvent[]>;
  recall: (incidentId: string) => Promise<MemoryRecallResponse>;

  demoStatus: () => Promise<DemoStatus>;
  demoScenario: () => Promise<DemoScenario>;
  demoRun: () => Promise<DemoRunResponse>;
  demoReset: () => Promise<Json>;
  demoHistory: () => Promise<Json>;
}

export function buildApi(base: string): Endpoints {
  return {
    health: () => request(base, "/api/health"),
    metrics: () => request(base, "/api/metrics/overview"),

    listIncidents: (query) =>
      request(base, `/api/incidents${query ? `?${query}` : ""}`),
    getIncident: (id) => request(base, `/api/incidents/${encodeURIComponent(id)}`),
    createIncident: (payload) => request(base, "/api/incidents", { method: "POST", json: payload }),
    incidentHistory: (id) =>
      request(base, `/api/incidents/${encodeURIComponent(id)}/history`),

    investigate: (id, memoryEnabled) =>
      request(base, `/api/incidents/${encodeURIComponent(id)}/investigate`, {
        method: "POST",
        json: { memory_enabled: memoryEnabled },
      }),
    simulateAction: (id, payload) =>
      request(base, `/api/incidents/${encodeURIComponent(id)}/simulate-action`, {
        method: "POST",
        json: payload,
      }),
    resolve: (id, payload) =>
      request(base, `/api/incidents/${encodeURIComponent(id)}/resolve`, {
        method: "POST",
        json: payload,
      }),
    retain: (id) =>
      request(base, `/api/incidents/${encodeURIComponent(id)}/retain`, { method: "POST" }),

    recentMemories: (limit = 5) => request(base, `/api/memory/recent?limit=${limit}`),
    recall: (incidentId) =>
      request(base, "/api/memory/recall", {
        method: "POST",
        json: { incident_id: incidentId },
      }),

    demoStatus: () => request(base, "/api/demo/status"),
    demoScenario: () => request(base, "/api/demo/scenarios"),
    demoRun: () => request(base, "/api/demo/run", { method: "POST" }),
    demoReset: () => request(base, "/api/demo/reset", { method: "POST" }),
    demoHistory: () => request(base, "/api/demo/history"),
  };
}
