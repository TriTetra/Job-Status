/**
 * Applications API client — CRUD for the application pipeline.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (typeof window !== "undefined") {
    const clerk = (window as any).Clerk;
    const token = await clerk?.session?.getToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...init,
    headers,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${path}: ${res.status} ${text}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export type ApplicationStatus =
  | "to_apply"
  | "applied"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Application {
  url: string;
  title: string;
  company: string | null;
  status: ApplicationStatus;
  applied_at: string | null;
  notes: string | null;
}

export const applicationsApi = {
  list: (status?: ApplicationStatus) => {
    const q = status ? `?status=${status}` : "";
    return apiFetch<Application[]>(`/api/applications/${q}`);
  },

  summary: () => apiFetch<Record<string, number>>("/api/applications/summary"),

  create: (data: {
    url: string;
    title: string;
    company?: string;
    status?: ApplicationStatus;
  }) =>
    apiFetch<Application>("/api/applications/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  update: (url: string, data: { status: ApplicationStatus; notes?: string | null }) =>
    apiFetch<Application>(`/api/applications/${encodeURIComponent(url)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
};
