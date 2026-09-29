import { buildApi } from "./api-core";

/**
 * Browser-side binding. Requests go to the Next rewrite (`/backend/*`), which
 * proxies to the backend, so the browser only ever talks to one origin.
 */
export const api = buildApi("/backend");
export { ApiError } from "./api-core";
