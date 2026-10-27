/**
 * Server-side client for the FastAPI backend (Server Components, route handlers).
 *
 * Authenticates with the signed-in user's Clerk session token. Responses are
 * per-user, so they are never cached (`fetch` is uncached by default in Next 16;
 * `no-store` makes that explicit).
 */

import "server-only";

import { auth } from "@clerk/nextjs/server";

import { parseResponse } from "./shared";

export { ApiError } from "./shared";

// Server-to-server calls may use an internal URL (e.g. inside Docker); fall back to the public one.
const SERVER_API_BASE = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function serverApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { getToken } = await auth();
  const token = await getToken();

  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${SERVER_API_BASE}${path}`, { cache: "no-store", ...init, headers });
  return parseResponse<T>(path, res);
}
