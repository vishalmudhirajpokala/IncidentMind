import * as path from "node:path";

import type { NextConfig } from "next";

const API = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The backend sits in a sibling directory, so without this Next traces the
  // whole workspace and warns about the extra lockfile it finds there.
  outputFileTracingRoot: path.join(import.meta.dirname, ".."),
  // The backend runs on a fixed port in development. Proxying through Next
  // means the browser only ever talks to one origin, so there is no CORS
  // preflight in the happy path and no hard-coded API host in client code.
  async rewrites() {
    return [{ source: "/backend/:path*", destination: `${API}/:path*` }];
  },
};

export default nextConfig;
