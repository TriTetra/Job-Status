"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { LabelText } from "@/components/shared/label-text";

export interface EvidenceSignal {
  text: string;
}

export interface EvidenceBlockProps {
  signalCount: number;
  signals: EvidenceSignal[];
  confidence: "High" | "Medium" | "Low";
  className?: string;
}

const confidenceColor: Record<EvidenceBlockProps["confidence"], string> = {
  High:   "var(--success)",
  Medium: "var(--accent)",
  Low:    "var(--text-muted)",
};

export function EvidenceBlock({
  signalCount,
  signals,
  confidence,
  className,
}: EvidenceBlockProps) {
  return (
    <div className={cn("space-y-6", className)}>
      <NarrativeText size="lg">
        We found{" "}
        <span className="font-medium" style={{ color: "var(--text-primary)" }}>
          {signalCount} signals
        </span>
        .
      </NarrativeText>

      <div className="space-y-1">
        {signals.map((signal, i) => (
          <div
            key={i}
            className="group/signal flex items-start gap-3 text-base p-2 -mx-2 rounded-md transition-colors duration-150 hover:bg-surface-hover"
            style={{ color: "var(--text-secondary)" }}
          >
            <span
              className="shrink-0 mt-1.5 transition-transform duration-150 group-hover/signal:scale-125"
              style={{ color: "var(--accent)" }}
            >
              •
            </span>
            <span className="leading-relaxed">{signal.text}</span>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 pt-2">
        <LabelText>Confidence</LabelText>
        <span
          className="text-base font-medium font-mono"
          style={{ color: confidenceColor[confidence] }}
        >
          {confidence}
        </span>
      </div>
    </div>
  );
}
