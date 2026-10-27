import { apiFetch } from "@/lib/api/client";
/**
 * Applications API client — CRUD for the application pipeline.
 */

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

/** Statuses still on the board (the pipeline columns); rejected / withdrawn are terminal. */
export const ACTIVE_STATUSES: ApplicationStatus[] = ["to_apply", "applied", "interview", "offer"];

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
    notes?: string;
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
