import type { Opportunity, ScanJob, ScanStatusResponse, Tier } from "./types";

/** Decision tier, with a fallback for rows scored before Decision Contract v1. */
export function tierOf(job: Opportunity): Tier {
  if (job.decision) return job.decision.semantic.tier;
  if (job.recommendation === "APPLY") return "strong";
  if (job.recommendation === "SKIP") return "low";
  return "look";
}

export function groupByTier(jobs: Opportunity[]): Record<Tier, Opportunity[]> {
  const groups: Record<Tier, Opportunity[]> = { strong: [], look: [], low: [] };
  for (const job of jobs) groups[tierOf(job)].push(job);
  return groups;
}

/** Backend scan status → the overlay's state. */
export function toScanJob(st: ScanStatusResponse): ScanJob {
  const phase: ScanJob["phase"] =
    st.status === "scanning" ? "fetch" : st.status === "scoring" ? "score" : st.status === "profile" ? "profile" : "starting";
  return {
    job_id: st.job_id,
    status: st.status === "completed" ? "done" : st.status === "failed" ? "failed" : "running",
    phase,
    progress: st.progress ?? 0,
    logs: st.logs ?? [],
    result: st.result ?? undefined,
    error: st.error ?? undefined,
  };
}
