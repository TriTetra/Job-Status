"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { onboardingApi, STEP_ORDER } from "@/features/onboarding";
import { NarrativeText } from "@/components/shared/narrative-text";
import { AplioLogo } from "@/components/shared/aplio-logo";
import { CareerGraph } from "./career-graph";
import { ExtractionLog } from "./extraction-log";

interface StepBuildingProps {
  onComplete: () => void;
}

export function StepBuilding({ onComplete }: StepBuildingProps) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);

  useEffect(() => {
    onboardingApi.buildGraph().then((r) => setJobId(r.job_id)).catch(console.error);
  }, []);

  useEffect(() => {
    if (!jobId) return;
    const t = setInterval(async () => {
      try {
        const r = await onboardingApi.getGraphStatus(jobId);
        setStatus(r);
        if (r.status === "completed") {
          clearInterval(t);
          setGraphData(r.result);
          setTimeout(() => onComplete(), 3500);
        } else if (r.status === "failed") {
          clearInterval(t);
          console.error("Graph failed:", r.error);
        }
      } catch (e) {
        clearInterval(t);
        console.error(e);
      }
    }, 800);
    return () => clearInterval(t);
  }, [jobId, onComplete]);

  const stepIdx = STEP_ORDER.indexOf("BUILDING" as any);

  return (
    <div className="w-full">
      {/* Üst bar — WizardShell ile aynı dil */}
      <div className="flex items-center justify-between mb-8">
        <AplioLogo variant="wordmark" size="md" />
        {stepIdx >= 0 && (
          <p className="text-[11px] font-medium tracking-widest uppercase text-[var(--text-muted)]">
            Step {stepIdx + 1} / {STEP_ORDER.length}
          </p>
        )}
      </div>

      {/* Split: sol süreç · sağ sonuç */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        {/* ── Sol: progress + log + stats ── */}
        <div className="space-y-4">
          <div>
            <NarrativeText size="xl" weight="semibold">Building your Career Graph.</NarrativeText>
            {status && (
              <p className="text-[13px] mt-0.5 text-[var(--text-muted)]">{status.progress}% complete</p>
            )}
          </div>

          {status && (
            <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--surface-hover)" }}>
              <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${status.progress}%`, background: "var(--accent)" }} />
            </div>
          )}

          {status && <ExtractionLog logs={status.logs} />}

          {status?.status === "completed" && graphData?.stats && (
            <div className="flex gap-8 pt-2">
              <div>
                <div className="text-xl font-semibold" style={{ color: "var(--accent)" }}>{graphData.stats.skills_count}</div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Skills</div>
              </div>
              <div>
                <div className="text-xl font-semibold" style={{ color: "var(--success)" }}>{graphData.stats.projects_count}</div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Projects</div>
              </div>
              <div>
                <div className="text-xl font-semibold" style={{ color: "var(--warning, #e6a817)" }}>
                  {graphData.stats.achievements_count ?? 0}
                </div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Honors</div>
              </div>
              <div>
                <div className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
                  {Math.round((graphData.stats.confidence_score || 0) * 100)}%
                </div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Confidence</div>
              </div>
            </div>
          )}

          {status?.status === "completed" && (
            <div className="animate-fade-in">
              <NarrativeText size="base" weight="semibold" className="text-[var(--success)]">
                Your Career Graph is ready.
              </NarrativeText>
              <p className="text-[12px] text-[var(--text-muted)]">Redirecting to your first briefing…</p>
            </div>
          )}
        </div>

        {/* ── Sağ: Career Graph (büyük) ── */}
        <div className="flex items-center justify-center">
          {graphData ? (
            <div className="w-full rounded-xl border border-[var(--border)] p-4" style={{ background: "var(--surface)" }}>
              <CareerGraph data={graphData} />
            </div>
          ) : (
            <div className="w-full aspect-[4/3] rounded-xl border border-dashed border-[var(--border)] flex flex-col items-center justify-center gap-3" style={{ background: "var(--surface)" }}>
              <div className="animate-spin h-7 w-7 border-2 border-[var(--accent)] border-t-transparent rounded-full" />
              <p className="text-xs text-[var(--text-muted)]">Compiling your evidence…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
