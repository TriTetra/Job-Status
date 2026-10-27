/**
 * Pieces shared by the browser and server API clients.
 * The FastAPI backend is the only data source for the web app.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Non-2xx response from the API. `status` lets callers branch (404 → empty state, 401 → sign in …). */
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
