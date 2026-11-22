"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Search, Zap } from "lucide-react";
import { Button } from "@/components/shared/button";
import { OpportunityCardCompact } from "@/components/ui/opportunity-card-compact";
import { OpportunityDetailPanel } from "@/components/ui/opportunity-detail-panel";
import { ScanOverlay } from "@/components/ui/scan-overlay";
import { opportunitiesApi } from "@/features/opportunities/api";
import { toScanJob } from "@/features/opportunities/tier";
import { byRank, companyOf, hasConflict, inView, rulesSentence, type View } from "@/features/opportunities/format";
import type { InboxData, Opportunity, ScanJob } from "@/features/opportunities/types";

const VIEWS: Array<{ id: View; label: string }> = [
  { id: "strong", label: "Strong" },
  { id: "look", label: "Worth a look" },
  { id: "all", label: "All" },
  { id: "shortlisted", label: "Shortlisted" },
  { id: "skipped", label: "Skipped" },
];

function lastScan(jobs: Opportunity[]): string | null {
  const latest = Math.max(...jobs.map((j) => (j.scanned_at ? Date.parse(j.scanned_at + (j.scanned_at.endsWith("Z") ? "" : "Z")) : 0)));
  if (!Number.isFinite(latest) || latest <= 0) return null;
  const mins = Math.round((Date.now() - latest) / 60_000);
  if (mins < 60) return `${Math.max(1, mins)} min ago`;
  const hours = Math.round(mins / 60);
  return hours < 48 ? `${hours} h ago` : `${Math.round(hours / 24)} days ago`;
}

export function InboxView({ initial }: { initial: InboxData }) {
  const params = useSearchParams();
  const wantedJob = params.get("job");
  const wantsScan = params.get("scan") === "1";

  const [jobs, setJobs] = useState<Opportunity[]>(initial.jobs);
  const prefs = initial.prefs;
  const [view, setView] = useState<View>(() => {
    if (initial.jobs.some((j) => j.url === wantedJob)) return "all";
    return initial.jobs.some((j) => inView(j, "strong")) ? "strong" : "all";
  });
  const [query, setQuery] = useState("");
  const [hideConflicts, setHideConflicts] = useState(true);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(
    () => initial.jobs.find((j) => j.url === wantedJob)?.url ?? null,
  );
  const [busy, setBusy] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [scanJob, setScanJob] = useState<ScanJob>({ job_id: "", status: "idle", phase: "starting", progress: 0, logs: [] });

  const refresh = useCallback(async () => {
    try {
      setJobs((await opportunitiesApi.list()).jobs);
    } catch (err) {
      console.error("[inbox] refresh failed:", err);
    }
  }, []);

  // ── scan ──
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

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

  // ?scan=1 (from the briefing) starts a scan once
  const autoScanned = useRef(false);
  useEffect(() => {
    if (!wantsScan || autoScanned.current) return;
    autoScanned.current = true;
    void handleScan();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on arrival
  }, [wantsScan]);

  // ── what's shown ──
  const counts = useMemo(() => {
    const c = {} as Record<View, number>;
    for (const v of VIEWS) c[v.id] = jobs.filter((j) => inView(j, v.id)).length;
    return c;
  }, [jobs]);

  const filtersConflicts = hideConflicts && view !== "skipped" && view !== "shortlisted";
  const conflictsHidden = useMemo(
    () => (filtersConflicts ? jobs.filter((j) => inView(j, view) && hasConflict(j)).length : 0),
    [jobs, view, filtersConflicts],
  );

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return jobs
      .filter((j) => inView(j, view))
      .filter((j) => !(filtersConflicts && hasConflict(j)))
      .filter((j) => !q || `${companyOf(j)} ${j.explanation?.title ?? ""}`.toLowerCase().includes(q))
      .sort(byRank);
  }, [jobs, view, query, filtersConflicts]);

  const selected = shown.find((j) => j.url === selectedUrl) ?? shown[0] ?? null;

  // ── decisions ──
  const handleDecision = async (url: string, status: "to_apply" | "applied" | "skipped") => {
    setDecisionError(null);
    setBusy(true);
    const idx = shown.findIndex((j) => j.url === url);
    try {
      await opportunitiesApi.decide(url, status);
      await refresh();
      // Skipping moves on to the next job in the list
      if (status === "skipped") setSelectedUrl(shown[idx + 1]?.url ?? shown[idx - 1]?.url ?? null);
    } catch (err) {
      console.error("[inbox] decision failed:", err);
      setDecisionError("That didn't save. Try again.");
    } finally {
      setBusy(false);
    }
  };

  // ↑ / ↓ move through the list
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      e.preventDefault();
      const i = shown.findIndex((j) => j.url === selected?.url);
      const next = shown[e.key === "ArrowUp" ? i - 1 : i + 1];
      if (next) setSelectedUrl(next.url);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [shown, selected]);

  const rules = rulesSentence(prefs);
  const scanned = lastScan(jobs);

  return (
    <div className="wide-container px-6 lg:px-8 py-10">
      {/* Header: the search as one sentence */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-[760px]">
          <h1 className="font-serif-display text-4xl" style={{ color: "var(--text-primary)" }}>Opportunities</h1>
          {rules && (
            <p className="mt-3 text-base leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {rules}{" "}
              <Link href="/settings?tab=preferences" className="text-sm whitespace-nowrap" style={{ color: "var(--accent)" }}>
                Change
              </Link>
            </p>
          )}
          <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
            {jobs.length} open matches · {counts.strong} strong
            {scanned ? ` · scored ${scanned}` : ""} · boards re-read every 6 hours
          </p>
        </div>
        <Button variant="outline" size="md" onClick={handleScan} disabled={scanJob.status === "running"}>
          <Zap className="h-4 w-4" />
          Rescore now
        </Button>
      </div>

      {/* Views + search + conflict filter */}
      <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 border-b pb-3" style={{ borderColor: "var(--border)" }}>
        <nav className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Views">
          {VIEWS.map((v) => {
            const active = v.id === view;
            return (
              <button
                key={v.id}
                onClick={() => {
                  setView(v.id);
                  setSelectedUrl(null);
                }}
                aria-current={active ? "page" : undefined}
                className="text-sm transition-colors"
                style={{ color: active ? "var(--text-primary)" : "var(--text-muted)", fontWeight: active ? 600 : 400 }}
              >
                {v.label} <span className="font-mono text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>{counts[v.id]}</span>
              </button>
            );
          })}
        </nav>
        <label className="ml-auto flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
          <Search className="h-4 w-4" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Company or title"
            aria-label="Search company or title"
            className="w-44 bg-transparent border-0 border-b outline-none py-1 text-sm focus:border-[var(--accent)]"
            style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </label>
        {view !== "skipped" && view !== "shortlisted" && (
          <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-muted)" }}>
            <input type="checkbox" checked={hideConflicts} onChange={(e) => setHideConflicts(e.target.checked)}
                   className="accent-[var(--accent)]" />
            Hide conflicts with my priorities{conflictsHidden ? ` (${conflictsHidden})` : ""}
          </label>
        )}
      </div>

      {decisionError && (
        <p className="mt-4 text-sm" role="alert" style={{ color: "var(--danger)" }}>{decisionError}</p>
      )}

      {/* List + decision panel: each scrolls in its own column */}
      {shown.length === 0 ? (
        <div className="py-20 text-center max-w-md mx-auto">
          <p className="font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>
            {jobs.length === 0 ? "No matches yet." : "Nothing in this view."}
          </p>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            {jobs.length === 0
              ? "Run a scan to match your evidence against open roles from 74 company boards."
              : conflictsHidden
                ? `${conflictsHidden} hidden because they conflict with your priorities.`
                : "Try another view or clear the search."}
          </p>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-[380px_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-8 lg:h-[calc(100vh-300px)]">
          <div className="max-h-[60vh] lg:max-h-none lg:min-h-0 overflow-y-auto custom-scrollbar -mx-2 px-2 space-y-0.5">
            {shown.map((opp) => (
              <OpportunityCardCompact
                key={opp.url}
                opp={opp}
                selected={selected?.url === opp.url}
                onClick={() => setSelectedUrl(opp.url)}
              />
            ))}
          </div>
          <div className="rounded-xl border overflow-hidden lg:min-h-0" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            {selected && (
              <OpportunityDetailPanel
                key={selected.url}
                opp={selected}
                busy={busy}
                onApply={() => handleDecision(selected.url, "applied")}
                onShortlist={() => handleDecision(selected.url, "to_apply")}
                onSkip={() => handleDecision(selected.url, "skipped")}
              />
            )}
          </div>
        </div>
      )}

      <ScanOverlay
        job={scanJob}
        onDismiss={() => setScanJob((prev) => ({ ...prev, status: "idle" }))}
        onRetry={handleScan}
      />
    </div>
  );
}
