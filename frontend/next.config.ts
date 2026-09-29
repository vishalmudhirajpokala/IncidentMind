import * as path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The backend sits in a sibling directory, so without this Next traces the
  // whole workspace and warns about the extra lockfile it finds there.
  outputFileTracingRoot: path.join(import.meta.dirname, ".."),
};

export default nextConfig;
