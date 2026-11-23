import { apiFetch } from "@/lib/api/client";
/**
 * Applications API client: the pipeline board, its analytics, and moving / noting / removing an application.
 */

export type ApplicationStatus =
  | "to_apply"
  | "applied"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface HistoryEvent {
  status: ApplicationStatus | "skipped";
  at: string;
}

/** One row of GET /api/applications/ (careeros/applications/pipeline.py::pipeline). */
export interface Application {
  url: string;
  title: string;
  company: string | null;
  company_key: string | null;
  status: ApplicationStatus;
  applied_at: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  history: HistoryEvent[];
  days_in_status: number | null;
  /** Applied two weeks ago or more with no answer yet */
  stale: boolean;
  location: string | null;
  remote: boolean;
  posting_closed: boolean;
  application_url: string;
  score: number | null;
  recommendation: string | null;
  /** careeros/applications/followup.py::state */
  follow_up?: FollowUpState | null;
}

export interface FollowUpState {
  /** 1: the first follow-up (14 days), 2: the last check-in (21 days), null: nothing due */
  due: 1 | 2 | null;
  sent: number;
  skipped: boolean;
  last_sent_at: string | null;
  draft_id: number | null;
  days_waiting: number | null;
}

export interface FollowUpDraft {
  id: number;
  url: string;
  step: 1 | 2;
  subject: string;
  body: string;
  generated_at: string | null;
  sent_at: string | null;
  /** claims the evidence doesn't support */
  check: string[];
  drafted_by: "llm" | "template" | null;
}

/** GET /api/applications/analytics (careeros/applications/pipeline.py::analytics). */
export interface ApplicationAnalytics {
  open_matches: number;
  funnel: Array<{ stage: "tracked" | "applied" | "interview" | "offer"; count: number }>;
  interview_rate: number | null;
  offer_rate: number | null;
  weekly_applied: number[];
  applied_this_week: number;
  response: { rate: number | null; answered: number; sent: number };
  waiting: { count: number; median_days: number | null; stale: number };
  by_score: Array<{ band: string; applied: number; interviews: number }>;
  closed: { rejected: number; withdrawn: number };
  passed_on: number;
}

/** Statuses still on the board (the pipeline columns); rejected / withdrawn are closed. */
export const ACTIVE_STATUSES: ApplicationStatus[] = ["to_apply", "applied", "interview", "offer"];
export const CLOSED_STATUSES: ApplicationStatus[] = ["rejected", "withdrawn"];

const path = (url: string) => `/api/applications/${encodeURIComponent(url)}`;

export const applicationsApi = {
  list: () => apiFetch<Application[]>("/api/applications/"),

  summary: () => apiFetch<Record<string, number>>("/api/applications/summary"),

  analytics: () => apiFetch<ApplicationAnalytics>("/api/applications/analytics"),

  create: (data: { url: string; title: string; company?: string; status?: ApplicationStatus; notes?: string }) =>
    apiFetch<unknown>("/api/applications/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  move: (url: string, status: ApplicationStatus) =>
    apiFetch<unknown>(path(url), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),

  setNotes: (url: string, notes: string) =>
    apiFetch<unknown>(path(url), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    }),

  remove: (url: string) => apiFetch<void>(path(url), { method: "DELETE" }),

  followUpDraft: (url: string, refresh = false) =>
    apiFetch<FollowUpDraft>("/api/applications/follow-ups/draft", { method: "POST", body: JSON.stringify({ url, refresh }) }),
  followUpSent: (id: number) => apiFetch<FollowUpDraft>(`/api/applications/follow-ups/${id}/sent`, { method: "POST" }),
  followUpSkip: (url: string) =>
    apiFetch<void>("/api/applications/follow-ups/skip", { method: "POST", body: JSON.stringify({ url }) }),
};
