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

  // Pass /api/jobs/ through untouched. Next would 308 it to /api/jobs, FastAPI would
  // 307 it back to /api/jobs/ on its internal host (http://api:8000/…), which the
  // browser can't reach.
  skipTrailingSlashRedirect: true,

  // Single public origin: the browser calls /api/* here, Next forwards it to FastAPI.
  // The session cookie stays first-party and the API is never exposed directly.
  async rewrites() {
    return [
      // `:path*` drops a trailing slash, so keep it with its own rule (first match wins)
      { source: "/api/:path*/", destination: `${API_URL}/api/:path*/` },
      { source: "/api/:path*", destination: `${API_URL}/api/:path*` },
    ];
  },
};

export default nextConfig;
