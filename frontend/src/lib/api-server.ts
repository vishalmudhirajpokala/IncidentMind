import "server-only";

import { buildApi } from "./api-core";

/**
 * Server-side binding. Server components and route handlers talk to the
 * backend directly; the internal URL never reaches the client bundle.
 */
const base = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

export const api = buildApi(base);

/**
 * The configured backend address, for offline messages.
 *
 * Naming the real address matters: telling an operator to start the backend on
 * a port this deployment does not use sends them to debug the wrong thing. The
 * host and port are not secrets — only credentials are, and those never leave
 * the backend.
 */
export const backendLabel = base;

export { ApiError } from "./api-core";
