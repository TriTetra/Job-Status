import { apiFetch } from "@/lib/api/client";

import type { InboxPreferences, OpportunityListResponse, ScanStatusResponse, UserDecisionStatus } from "./types";

export const ALL_OPPORTUNITIES = "/api/jobs/?recommendation=ALL&limit=500";

export const opportunitiesApi = {
  list: () => apiFetch<OpportunityListResponse>(ALL_OPPORTUNITIES),
  preferences: () => apiFetch<InboxPreferences>("/api/preferences"),
  startScan: () => apiFetch<{ job_id: string }>("/api/jobs/scan", { method: "POST" }),
  scanStatus: (jobId: string) => apiFetch<ScanStatusResponse>(`/api/jobs/scan/${jobId}/status`),
  /** Shortlist / Apply / Skip — creates the application if it doesn't exist yet. */
  decide: (url: string, status: "to_apply" | "applied" | "skipped") =>
    apiFetch<{ status: UserDecisionStatus; decided_at: string }>("/api/jobs/decide", {
      method: "POST",
      body: JSON.stringify({ url, status }),
    }),
};
