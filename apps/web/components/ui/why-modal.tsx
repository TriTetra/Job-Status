"use client";

import type { Opportunity } from "@/features/opportunities/types";
import { NarrativeText } from "@/components/shared/narrative-text";
import { X } from "lucide-react";

interface WhyModalProps {
  opp: Opportunity;
  onClose: () => void;
}

/**
 * Explainability modal — "Why 82?"
 * Shows scoring breakdown + weights from Settings.
 */
export function WhyModal({ opp, onClose }: WhyModalProps) {
  const breakdown = [
    { label: "Fit", value: opp.fit_score ?? 0 },
    { label: "Career value", value: opp.career_value ?? 0 },
    { label: "Market demand", value: opp.market_demand ?? 0 },
    { label: "Acceptance", value: opp.acceptance_probability ?? 0 },
  ];

  const total = breakdown.reduce((sum, b) => sum + b.value, 0);
  const avg = Math.round(total / breakdown.length);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className="relative w-full max-w-lg rounded-xl border p-8"
        style={{
          background: "var(--surface-elevated)",
          borderColor: "var(--border-strong)",
          boxShadow: "0 24px 48px rgba(0,0,0,0.4)",
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-md hover:bg-[var(--surface-hover)] transition-colors bg-transparent border-0 cursor-pointer"
        >
          <X className="h-5 w-5" style={{ color: "var(--text-muted)" }} />
        </button>

        {/* Header */}
        <NarrativeText size="xl" weight="semibold" className="mb-1">
          Why {opp.career_score ?? avg}?
        </NarrativeText>
        <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
          Scoring breakdown and weights
        </p>

        {/* Breakdown */}
        <div className="space-y-3 mb-6">
          {breakdown.map((b) => (
            <div key={b.label} className="flex items-center justify-between">
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {b.label}
              </span>
              <span
                className="font-mono text-sm font-semibold tabular-nums"
                style={{ color: "var(--text-primary)" }}
              >
                {Math.round(b.value)}
              </span>
            </div>
          ))}
          <div className="pt-3 border-t" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Overall
              </span>
              <span
                className="font-mono text-lg font-bold tabular-nums"
                style={{ color: "var(--accent)" }}
              >
                {opp.career_score ?? avg}
              </span>
            </div>
          </div>
        </div>

        {/* Weights note */}
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          These weights are set in your Settings. You weight fit{" "}
          {(opp.fit_score ?? 0) > 50 ? "heavily" : "moderately"}.
        </p>
      </div>
    </div>
  );
}
