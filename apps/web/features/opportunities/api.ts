import { apiFetch } from "@/lib/api/client";

import type { SkipReason } from "./format";
import type { InboxPreferences, Opportunity, OpportunityListResponse, ScanStatusResponse, UserDecisionStatus } from "./types";

export const ALL_OPPORTUNITIES = "/api/jobs/?recommendation=ALL&limit=500";

/** A job the person added (careeros/jobs/added.py); `own` = their private copy, else a known shared job. */
export interface AddedJob {
  url: string;
  title: string;
  company: string;
  location: string;
  own: boolean;
  career_score: number | null;
  recommendation: string | null;
}

export const opportunitiesApi = {
  list: () => apiFetch<OpportunityListResponse>(ALL_OPPORTUNITIES),
  preferences: () => apiFetch<InboxPreferences>("/api/preferences"),
  startScan: () => apiFetch<{ job_id: string }>("/api/jobs/scan", { method: "POST" }),
  scanStatus: (jobId: string) => apiFetch<ScanStatusResponse>(`/api/jobs/scan/${jobId}/status`),
  /** Add any job by link (read where allowed) or pasted text; scored for this person only. */
  add: (url: string, text?: string) =>
    apiFetch<AddedJob>("/api/jobs/add", { method: "POST", body: JSON.stringify({ url, text: text ?? null }) }),
  /** Shortlist / Apply / Skip — creates the application if it doesn't exist yet. */
  decide: (url: string, status: "to_apply" | "applied" | "skipped",
           opts: { reasons?: SkipReason[]; surface?: "inbox" | "search" | "queue"; shown?: Opportunity } = {}) =>
    apiFetch<{ status: UserDecisionStatus; decided_at: string }>("/api/jobs/decide", {
      method: "POST",
      body: JSON.stringify({
        url, status, reasons: opts.reasons ?? [], surface: opts.surface,
        // what the screen showed: the context of the decision, for learning
        shown_score: opts.shown?.career_score ?? null,
        shown_p_interview: opts.shown?.explanation?.model?.p_effective ?? null,
        shown_value: opts.shown?.explanation?.model?.value ?? null,
      }),
    }),
};
