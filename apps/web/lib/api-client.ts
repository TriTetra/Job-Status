/**
 * Canonical client for the FastAPI backend (browser side).
 *
 * Every API route requires a signed-in user, so each request carries the
 * Clerk session token as a Bearer header. Feature modules should use this
 * instead of their own fetch wrappers.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${path}: ${res.status} ${text}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}
