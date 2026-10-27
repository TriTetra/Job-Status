/**
 * Server-side client for the FastAPI backend (Server Components).
 *
 * Calls the API directly on the internal network (API_URL) and forwards the
 * signed-in user's session cookie. Responses are per-user, so never cached.
 */

import "server-only";

import { cookies } from "next/headers";

import { parseResponse, withCsrf } from "./shared";

export { ApiError } from "./shared";

const SERVER_API_BASE = process.env.API_URL ?? "http://localhost:8000";

export async function serverApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = withCsrf(new Headers(init?.headers), init?.method);
  const cookieHeader = (await cookies()).toString();
  if (cookieHeader) headers.set("Cookie", cookieHeader);

  const res = await fetch(`${SERVER_API_BASE}${path}`, { cache: "no-store", ...init, headers });
  return parseResponse<T>(path, res);
}
