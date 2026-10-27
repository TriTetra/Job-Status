/**
 * Browser client for the FastAPI backend.
 *
 * Same-origin requests: the httpOnly session cookie travels automatically,
 * and state-changing calls carry the CSRF header. Feature modules import
 * this; never write another fetch wrapper.
 */

import { API_BASE, parseResponse, withCsrf } from "./shared";

export { API_BASE, ApiError } from "./shared";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = withCsrf(new Headers(init?.headers), init?.method);
  const res = await fetch(`${API_BASE}${path}`, { credentials: "same-origin", ...init, headers });
  return parseResponse<T>(path, res);
}
