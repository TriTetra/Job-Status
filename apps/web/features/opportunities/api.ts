import { apiFetch } from "@/lib/api/client";

import type { InboxPreferences, OpportunityListResponse, ScanStatusResponse, UserDecisionStatus } from "./types";

export const ALL_OPPORTUNITIES = "/api/jobs/?recommendation=ALL&limit=500";

export const opportunitiesApi = {
  list: () => apiFetch<OpportunityListResponse>(ALL_OPPORTUNITIES),
  preferences: () => apiFetch<InboxPreferences>("/api/preferences"),
  startScan: () => apiFetch<{ job_id: string }>("/api/jobs/scan?limit=200", { method: "POST" }),
  scanStatus: (jobId: string) => apiFetch<ScanStatusResponse>(`/api/jobs/scan/${jobId}/status`),
  /** Records the user's decision as an application status (to_apply | applied | skipped …). */
  decide: (url: string, status: UserDecisionStatus | string) =>
    apiFetch(`/api/applications/${encodeURIComponent(url)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),
};
