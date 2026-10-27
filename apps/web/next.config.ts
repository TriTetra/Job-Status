import type { NextConfig } from "next";

/**
 * The backend's address on the internal network. Rewrites are resolved at
 * build time, so API_URL must be set when running `next build` (the Docker
 * build passes it in; locally it defaults to the dev API on :8000).
 */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image (.next/standalone)
  output: "standalone",

  // Single public origin: the browser calls /api/* here, Next forwards it to FastAPI.
  // The session cookie stays first-party and the API is never exposed directly.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
