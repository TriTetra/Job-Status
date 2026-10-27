/**
 * Browser client for the FastAPI backend.
 *
 * Every API route requires a signed-in user, so each request carries the
 * current Clerk session token (fresh per call — the SDK refreshes it).
 * Feature modules import this; never write another fetch wrapper.
 */

import { API_BASE, parseResponse } from "./shared";

export { API_BASE, ApiError } from "./shared";

type ClerkWindow = Window & {
  Clerk?: { session?: { getToken?: () => Promise<string | null> } };
};

async function sessionToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  return (await (window as ClerkWindow).Clerk?.session?.getToken?.()) ?? null;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const token = await sessionToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { credentials: "include", ...init, headers });
  return parseResponse<T>(path, res);
}
