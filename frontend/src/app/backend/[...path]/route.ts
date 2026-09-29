type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const FORWARDED_REQUEST_HEADERS = ["accept", "content-type", "x-request-id"];
const FORWARDED_RESPONSE_HEADERS = ["cache-control", "content-type", "x-request-id"];

async function forwardToBackend(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const incoming = new URL(request.url);
  const serviceBase = (process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const upstreamUrl = new URL(
    `${path.map((segment) => encodeURIComponent(segment)).join("/")}${incoming.search}`,
    `${serviceBase}/`,
  );
  const headers = new Headers();

  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const body = request.method === "GET" || request.method === "HEAD"
    ? undefined
    : await request.arrayBuffer();
  const upstream = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
    signal: request.signal,
  });
  const responseHeaders = new Headers();

  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  return new Response(upstream.status === 204 ? null : upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const dynamic = "force-dynamic";
export const GET = forwardToBackend;
export const POST = forwardToBackend;
export const PATCH = forwardToBackend;
export const DELETE = forwardToBackend;
