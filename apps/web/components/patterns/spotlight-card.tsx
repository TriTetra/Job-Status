"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { ArrowRight } from "lucide-react";

export type Recommendation = "APPLY" | "CONSIDER" | "SKIP";

export interface SpotlightCardProps {
  company: string;
  role: string;
  location: string;
  score: number;
  recommendation: Recommendation;
  why: string[];
  gap?: string;
  onApply?: () => void;
  onGenerateResume?: () => void;
  onWhy?: () => void;
  className?: string;
}

const recColor: Record<Recommendation, string> = {
  APPLY:    "var(--success)",
  CONSIDER: "var(--accent)",
  SKIP:     "var(--text-muted)",
};

/**
 * Borderless editorial opportunity. No card chrome — pure typography.
 * Structure is felt through whitespace and one score accent, not a box.
 */
export function SpotlightCard({
  company,
  role,
  location,
  score,
  recommendation,
  why,
  gap,
  onApply,
  onGenerateResume,
  onWhy,
  className,
}: SpotlightCardProps) {
  return (
    <article className={cn("flex flex-col", className)}>
      {/* Company + score on one editorial line */}
      <div className="flex items-baseline gap-2 mb-0.5">
        <NarrativeText size="lg" weight="semibold" as="span">{company}</NarrativeText>
        <span className="font-mono text-sm font-semibold tabular-nums" style={{ color: recColor[recommendation] }}>
          {score}
        </span>
        <span className="text-[10px] uppercase tracking-wider" style={{ color: recColor[recommendation] }}>
          {recommendation}
        </span>
      </div>

      <div className="text-sm mb-3" style={{ color: "var(--text-muted)" }}>
        {role} · {location}
      </div>

      {/* Why — one calm line */}
      <NarrativeText size="sm" className="mb-1" style={{ color: "var(--text-secondary)" }}>
        {why.join(", ")}.
      </NarrativeText>
      {gap && (
        <NarrativeText size="sm" className="mb-4" style={{ color: "var(--text-muted)" }}>
          Gap: {gap}.
        </NarrativeText>
      )}

      {/* Actions as text links, not buttons */}
      <div className="flex items-center gap-5 text-sm mt-auto">
        <button
          onClick={onApply}
          className="inline-flex items-center gap-1 font-medium transition-colors group/apply"
          style={{ color: "var(--accent)" }}
        >
          Apply
          <ArrowRight className="h-3.5 w-3.5 transition-transform duration-150 group-hover/apply:translate-x-0.5" strokeWidth={2} />
        </button>
        <button onClick={onGenerateResume} className="transition-colors" style={{ color: "var(--text-secondary)" }}>
          Generate resume
        </button>
        <button onClick={onWhy} className="ml-auto transition-colors" style={{ color: "var(--text-muted)" }}>
          Why {score}?
        </button>
      </div>
    </article>
  );
}
