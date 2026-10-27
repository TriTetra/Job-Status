"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { OpportunityCardCompact } from "@/components/ui/opportunity-card-compact";
import { OpportunityDetailPanel } from "@/components/ui/opportunity-detail-panel";
import { ScanOverlay } from "@/components/ui/scan-overlay";
import { Zap, Settings2, ChevronDown } from "lucide-react";
import { opportunitiesApi } from "@/features/opportunities/api";
import { groupByTier, toScanJob } from "@/features/opportunities/tier";
import type { InboxData, InboxPreferences, Opportunity, ScanJob } from "@/features/opportunities/types";

export function InboxView({ initial }: { initial: InboxData }) {
  const [jobs, setJobs] = useState<Opportunity[]>(initial.jobs);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(initial.jobs[0]?.url ?? null);
  const [loading, setLoading] = useState(false);
  const [lowFitExpanded, setLowFitExpanded] = useState(false);

  const [scanJob, setScanJob] = useState<ScanJob>({
    job_id: "",
    status: "idle",
    phase: "starting",
    progress: 0,
    logs: [],
  });

  const [prefs] = useState<InboxPreferences | null>(initial.prefs);

  // First render uses the server's list; this refreshes it after a scan or a decision
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setJobs((await opportunitiesApi.list()).jobs);
    } catch (err) {
      console.error("[inbox] refresh failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Scan polling stops when the page unmounts
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  // Scan handler
  const handleScan = async () => {
    setScanJob((prev) => ({ ...prev, status: "running", phase: "starting", progress: 0, logs: [] }));
    try {
      const { job_id } = await opportunitiesApi.startScan();
      setScanJob((prev) => ({ ...prev, job_id }));

      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const st = await opportunitiesApi.scanStatus(job_id);
          setScanJob(toScanJob(st));
          if (st.status === "completed" || st.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            if (st.status === "completed") await refresh();
          }
        } catch (err) {
          console.warn("[inbox] scan poll failed, retrying:", err);
        }
      }, 1200);
    } catch (err) {
      setScanJob((prev) => ({ ...prev, status: "failed", error: String(err) }));
    }
  };

  // Auto-advance: after Apply/Shortlist/Skip, move to next unreviewed
  const handleDecision = async (url: string, status: string) => {
    try {
      await opportunitiesApi.decide(url, status);
      // Reload to get updated user_decision
      await refresh();
      // Auto-advance: select next unreviewed job
      const currentIdx = jobs.findIndex((j) => j.url === url);
      const nextUnreviewed = jobs.slice(currentIdx + 1).find((j) => j.user_decision.status === "unreviewed");
      if (nextUnreviewed) {
        setSelectedUrl(nextUnreviewed.url);
      }
    } catch (err) {
      console.error("[inbox] decision failed:", err);
    }
  };

  // Group by tier (with a fallback for rows scored before Decision Contract v1)
  const grouped = useMemo(() => groupByTier(jobs), [jobs]);

  const selected = jobs.find((j) => j.url === selectedUrl) ?? null;

  // Build criteria chips for header
  const criteriaChips = useMemo(() => {
    const chips: string[] = [];
    if (prefs?.work_arrangements?.includes("remote")) chips.push("Remote");
    if (prefs?.preferred_country_codes?.length) {
      chips.push(prefs.preferred_country_codes.slice(0, 3).join(", "));
    }
    const sMin = prefs?.salary_min ?? prefs?.salary?.min;
    const sMax = prefs?.salary_max ?? prefs?.salary?.max;
    if (sMin || sMax) {
      chips.push(`€${sMin ?? 0}k+`);
    }
    if (prefs?.requires_sponsorship === false) chips.push("No visa");
    return chips;
  }, [prefs]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowUp" || e.key === "ArrowDown") {
        e.preventDefault();
        const currentIdx = jobs.findIndex((j) => j.url === selectedUrl);
        const nextIdx = e.key === "ArrowUp" ? currentIdx - 1 : currentIdx + 1;
        if (nextIdx >= 0 && nextIdx < jobs.length) {
          setSelectedUrl(jobs[nextIdx].url);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [jobs, selectedUrl]);

  return (
    <div className="wide-container px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <NarrativeText size="2xl" weight="semibold" className="mb-1">
            Opportunities
          </NarrativeText>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {jobs.length} scored · {grouped.strong.length} strong · {grouped.look.length} worth a look
          </p>
        </div>
        <Button variant="primary" size="md" onClick={handleScan} disabled={scanJob.status === "running"}>
          <Zap className="h-4 w-4" />
          Scan Now
        </Button>
      </div>

      {/* Criteria chips */}
      {criteriaChips.length > 0 && (
        <div className="mb-6 flex items-center gap-2 flex-wrap">
          {criteriaChips.map((chip) => (
            <span
              key={chip}
              className="px-3 py-1 rounded-full border text-xs font-medium"
              style={{
                borderColor: "var(--accent)",
                background: "rgba(255, 177, 98, 0.08)",
                color: "var(--accent)",
              }}
            >
              {chip}
            </span>
          ))}
          <Link
            href="/settings"
            className="flex items-center gap-1 text-xs font-medium transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <Settings2 className="h-3 w-3" />
            Edit
          </Link>
        </div>
      )}

      {/* Split-panel layout */}
      {loading ? (
        <div className="surface p-12 text-center">
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Loading opportunities…
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-8 h-[calc(100vh-280px)]">
          {/* Left: Scanner (compact list) */}
          <div className="overflow-y-auto custom-scrollbar pr-4 space-y-6">
            {grouped.strong.length > 0 && (
              <div className="space-y-2">
                <div
                  className="text-[11px] font-semibold tracking-wider uppercase px-2 mb-2"
                  style={{ color: "var(--success)", fontFamily: "var(--font-display)" }}
                >
                  Strong matches ({grouped.strong.length})
                </div>
                <div className="space-y-2">
                  {grouped.strong.map((opp) => (
                    <OpportunityCardCompact
                      key={opp.url}
                      opp={opp}
                      selected={selectedUrl === opp.url}
                      onClick={() => setSelectedUrl(opp.url)}
                    />
                  ))}
                </div>
              </div>
            )}

            {grouped.look.length > 0 && (
              <div className="space-y-2">
                <div
                  className="text-[11px] font-semibold tracking-wider uppercase px-2 mb-2"
                  style={{ color: "var(--text-secondary)", fontFamily: "var(--font-display)" }}
                >
                  Worth a look ({grouped.look.length})
                </div>
                <div className="space-y-2">
                  {grouped.look.map((opp) => (
                    <OpportunityCardCompact
                      key={opp.url}
                      opp={opp}
                      selected={selectedUrl === opp.url}
                      onClick={() => setSelectedUrl(opp.url)}
                    />
                  ))}
                </div>
              </div>
            )}

            {grouped.low.length > 0 && (
              <div className="space-y-2">
                <button
                  onClick={() => setLowFitExpanded(!lowFitExpanded)}
                  className="w-full text-left text-[11px] font-semibold tracking-wider uppercase px-2 flex items-center gap-2 transition-colors bg-transparent border-0 cursor-pointer mb-2"
                  style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
                >
                  Low fit ({grouped.low.length})
                  <ChevronDown
                    className={`h-3 w-3 transition-transform ${lowFitExpanded ? "rotate-180" : ""}`}
                  />
                </button>
                {lowFitExpanded && (
                  <div className="space-y-2">
                    {grouped.low.map((opp) => (
                      <OpportunityCardCompact
                        key={opp.url}
                        opp={opp}
                        selected={selectedUrl === opp.url}
                        onClick={() => setSelectedUrl(opp.url)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: Reader (detail panel) */}
          <div
            className="rounded-xl border overflow-hidden"
            style={{
              background: "var(--surface)",
              borderColor: "var(--border)",
              maxHeight: "calc(100vh - 280px)",
            }}
          >
            {selected ? (
              <OpportunityDetailPanel
                key={selected.url} // fresh panel state (fetched reasoning) per opportunity
                opp={selected}
                onApply={() => handleDecision(selected.url, "applied")}
                onShortlist={() => handleDecision(selected.url, "to_apply")}
                onSkip={() => handleDecision(selected.url, "skipped")}
              />
            ) : (
              <div className="flex items-center justify-center h-full p-12">
                <NarrativeText size="lg" weight="medium" className="text-center" style={{ color: "var(--text-muted)" }}>
                  Select an opportunity to see details
                </NarrativeText>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scan overlay */}
      <ScanOverlay
        job={scanJob}
        onDismiss={() => setScanJob((prev) => ({ ...prev, status: "idle" }))}
        onRetry={handleScan}
      />
    </div>
  );
}
