"use client";

import type { ScanJob, ScanPhase } from "@/features/opportunities/types";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

interface ScanOverlayProps {
  job: ScanJob;
  onDismiss: () => void;
  onRetry: () => void;
}

const PHASE_COPY: Record<ScanPhase, string> = {
  starting: "Reading your career graph.",
  profile: "Reading your career graph.",
  fetch: "Scanning live sources.",
  score: "Weighing every opportunity.",
};

/**
 * Scan state machine overlay.
 * States: idle (hidden) → running (phases + logs) → done (summary) → failed (error + retry)
 */
export function ScanOverlay({ job, onDismiss, onRetry }: ScanOverlayProps) {
  if (job.status === "idle") return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md rounded-xl border p-8"
        style={{
          background: "var(--surface-elevated)",
          borderColor: "var(--border-strong)",
          boxShadow: "0 24px 48px rgba(0,0,0,0.5)",
        }}
      >
        {job.status === "running" && (
          <>
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <Loader2 className="h-6 w-6 animate-spin" style={{ color: "var(--accent)" }} />
                <NarrativeText size="lg" weight="semibold">
                  Scanning opportunities
                </NarrativeText>
              </div>
              <p
                className="text-base italic"
                style={{ fontFamily: "var(--font-editorial)", color: "var(--text-secondary)" }}
              >
                {PHASE_COPY[job.phase]}
              </p>
            </div>

            {/* Progress bar */}
            <div className="h-1 rounded-full overflow-hidden mb-4" style={{ background: "var(--surface-hover)" }}>
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{ width: `${job.progress}%`, background: "var(--accent)" }}
              />
            </div>

            {/* Logs (mono, last 4) */}
            <div className="space-y-1 font-mono text-xs" style={{ color: "var(--text-muted)" }}>
              {job.logs.slice(-4).map((log, i) => (
                <div key={i}>{log.message}</div>
              ))}
            </div>
          </>
        )}

        {job.status === "done" && job.result && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 className="h-8 w-8" style={{ color: "var(--success)" }} />
              <NarrativeText size="xl" weight="semibold">
                {job.result.scored} opportunities deserve your attention.
              </NarrativeText>
            </div>
            <div className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
              {job.result.apply} strong · {job.result.consider} worth a look · {job.result.skip} low fit
            </div>
            <Button variant="primary" onClick={onDismiss} className="w-full">
              Continue
            </Button>
          </>
        )}

        {job.status === "failed" && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <XCircle className="h-8 w-8" style={{ color: "var(--danger)" }} />
              <NarrativeText size="xl" weight="semibold">
                Scan failed
              </NarrativeText>
            </div>
            <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
              {job.error ?? "An unexpected error occurred."}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onDismiss} className="flex-1">
                Dismiss
              </Button>
              <Button variant="primary" onClick={onRetry} className="flex-1">
                Retry
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
