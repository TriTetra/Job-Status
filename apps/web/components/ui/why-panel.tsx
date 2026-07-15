"use client";

import { useEffect } from "react";
import { X, Check, AlertCircle } from "lucide-react";
import { MetricText } from "@/components/shared/metric-text";
import { NarrativeText } from "@/components/shared/narrative-text";
import { LabelText } from "@/components/shared/label-text";

export interface BreakdownItem {
  label: string;
  value: number;
  positive: boolean;
  description?: string;
}

interface WhyPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  score?: number;
  breakdown: BreakdownItem[];
  baseScore?: number;
}

export function WhyPanel({
  isOpen,
  onClose,
  title,
  score,
  breakdown,
  baseScore = 50,
}: WhyPanelProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  if (!isOpen) return null;

  const positiveItems = breakdown.filter((i) => i.positive);
  const negativeItems = breakdown.filter((i) => !i.positive);
  const positiveTotal = positiveItems.reduce((s, i) => s + i.value, 0);
  const negativeTotal = negativeItems.reduce((s, i) => s + i.value, 0);
  const finalScore = score ?? baseScore + positiveTotal + negativeTotal;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0"
        style={{ background: "rgba(27,38,50,0.65)", backdropFilter: "blur(4px)" }}
        onClick={onClose}
      />
      <div
        className="absolute right-0 top-0 h-full w-full max-w-md flex flex-col"
        style={{ background: "var(--surface)", borderLeft: "1px solid var(--border-strong)", boxShadow: "0 0 40px rgba(0,0,0,0.4)" }}
      >
        {/* Header */}
        <div className="h-16 px-6 flex items-center justify-between border-b shrink-0" style={{ borderColor: "var(--border)" }}>
          <NarrativeText size="lg" weight="semibold">{title}</NarrativeText>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-colors hover:bg-[var(--surface-elevated)]"
            style={{ color: "var(--text-muted)" }}
            aria-label="Close"
          >
            <X className="h-4 w-4" strokeWidth={2} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Base score</span>
            <MetricText value={baseScore} size="lg" />
          </div>

          {positiveItems.length > 0 && (
            <div>
              <LabelText accent className="mb-3 block" style={{ color: "var(--success)" } as React.CSSProperties}>
                Positive adjustments
              </LabelText>
              <div className="space-y-1">
                {positiveItems.map((item, i) => (
                  <BreakdownRow key={i} item={item} />
                ))}
              </div>
            </div>
          )}

          {negativeItems.length > 0 && (
            <div>
              <LabelText className="mb-3 block" style={{ color: "var(--danger)" } as React.CSSProperties}>
                Gaps
              </LabelText>
              <div className="space-y-1">
                {negativeItems.map((item, i) => (
                  <BreakdownRow key={i} item={item} />
                ))}
              </div>
            </div>
          )}

          <div className="pt-4 border-t" style={{ borderColor: "var(--border)" }}>
            <LabelText className="mb-3 block">Calculation</LabelText>
            <div
              className="rounded-lg p-4 space-y-2 font-mono text-sm"
              style={{ background: "var(--surface-elevated)", border: "1px solid var(--border)" }}
            >
              <div className="flex justify-between">
                <span style={{ color: "var(--text-secondary)" }}>Base</span>
                <span style={{ color: "var(--text-primary)" }}>{baseScore}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "var(--success)" }}>+ Adjustments</span>
                <span style={{ color: "var(--success)" }}>+{positiveTotal}</span>
              </div>
              {negativeTotal !== 0 && (
                <div className="flex justify-between">
                  <span style={{ color: "var(--danger)" }}>− Gaps</span>
                  <span style={{ color: "var(--danger)" }}>−{Math.abs(negativeTotal)}</span>
                </div>
              )}
              <div className="pt-2 border-t flex justify-between font-semibold" style={{ borderColor: "var(--border)" }}>
                <span style={{ color: "var(--text-primary)" }}>Final score</span>
                <MetricText value={finalScore} size="md" />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="h-14 px-6 border-t flex items-center justify-between shrink-0" style={{ borderColor: "var(--border)" }}>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            Updates as your profile evolves
          </span>
          <button
            onClick={onClose}
            className="text-sm transition-colors"
            style={{ color: "var(--accent)" }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function BreakdownRow({ item }: { item: BreakdownItem }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <div className="mt-0.5 shrink-0">
        {item.positive
          ? <Check className="h-4 w-4" style={{ color: "var(--success)" }} strokeWidth={2.5} />
          : <AlertCircle className="h-4 w-4" style={{ color: "var(--danger)" }} strokeWidth={2} />
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm" style={{ color: "var(--text-primary)" }}>{item.label}</div>
        {item.description && (
          <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{item.description}</div>
        )}
      </div>
      <MetricText
        value={item.value}
        size="sm"
        trend={item.positive ? "up" : "down"}
        showTrendIcon={false}
      />
    </div>
  );
}
