import { apiFetch } from "@/lib/api/client";

/** Where a suggested answer comes from (careeros/applications/kit.py). */
export type AnswerSource = "profile" | "preferences" | "suggestion" | "draft" | "you" | "llm";

export interface KitQuestion {
  id: string;
  label: string;
  kind: "text" | "textarea" | "file" | "select" | "multiselect";
  required: boolean;
  options: string[];
  suggested: string | null;
  source: AnswerSource;
  note: string | null;
}

export interface Kit {
  v: number;
  url: string;
  title: string;
  company: string;
  location: string | null;
  apply_url: string;
  form: "greenhouse" | "standard";
  cv: { document_id: number; version: number; filename: string; ref: string } | null;
  score: number | null;
  p_interview: number | null;
  matched: string[];
  gaps: string[];
  warnings: string[];
  ai_policy: boolean;
  questions: KitQuestion[];
  cover_note: string | null;
  cover_note_check?: string[];
  drafted: boolean;
  created_at: string;
}

export interface QueueItem {
  url: string;
  title: string;
  company: string;
  location: string | null;
  company_key: string | null;
  score: number | null;
  recommendation: string | null;
  p_interview: number | null;
  apply_url: string;
  ready: boolean;
  kit: Kit | null;
}

export interface ReportApplication {
  url: string;
  title: string;
  company: string;
  company_key: string | null;
  status: string;
  state: string;
  days: number | null;
  chance_now?: number;
  chance_at_send?: number;
  posting_closed?: boolean;
}

export interface DailyReport {
  date: string;
  sent_this_week: number;
  counts: Record<string, number>;
  active: ReportApplication[];
  ghosted: number;
  queue: { url: string; title: string; company: string; score: number | null; p_interview: number | null; ready: boolean }[];
  learn: { skill: string; jobs: number }[];
  new_matches: number;
  new_good_matches: number;
}

export const applyApi = {
  queue: () => apiFetch<{ items: QueueItem[] }>("/api/apply/queue"),
  prepare: (url: string, refresh = false) =>
    apiFetch<{ kit: Kit }>("/api/apply/kit", { method: "POST", body: JSON.stringify({ url, refresh }) }),
  report: () => apiFetch<DailyReport>("/api/apply/report"),
};

export const SOURCE_LABEL: Record<AnswerSource, string> = {
  profile: "From your profile",
  preferences: "From your preferences",
  suggestion: "Suggested",
  draft: "Drafted from your evidence: read and edit it",
  you: "You answer this",
  llm: "You answer this",
};
