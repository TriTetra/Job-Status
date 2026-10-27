/**
 * Pieces shared by the browser and server API clients.
 * The FastAPI backend is the only data source for the web app.
 */

/**
 * The browser calls the API on its own origin: next.config.ts rewrites /api/*
 * to the backend, so the session cookie is first-party and there is no CORS.
 */
export const API_BASE = "";

/** Required by the API on every state-changing request (see apps/api/app/main.py). */
export const CSRF_HEADER = "X-CareerOS-CSRF";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

export function withCsrf(headers: Headers, method: string | undefined): Headers {
  if (!SAFE_METHODS.has((method ?? "GET").toUpperCase())) headers.set(CSRF_HEADER, "1");
  return headers;
}

/** Non-2xx response from the API. `status` lets callers branch (401 → sign in, 404 → empty state …). */
export class ApiError extends Error {
  constructor(
    readonly path: string,
    readonly status: number,
    readonly body: string,
  ) {
    super(`${path}: ${status} ${body}`);
    this.name = "ApiError";
  }
}

export async function parseResponse<T>(path: string, res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new ApiError(path, res.status, body);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}
