"use client";

import type { Opportunity } from "@/features/opportunities/types";
import { cn } from "@/lib/utils";

interface OpportunityCardCompactProps {
  opp: Opportunity;
  selected: boolean;
  onClick: () => void;
}

/**
 * Sol panel kartı — scanner.
 * Borderless editorial, mono score, sans medium.
 */
export function OpportunityCardCompact({ opp, selected, onClick }: OpportunityCardCompactProps) {
  const { decision, career_score } = opp;
  const tier = decision?.semantic.tier ?? "look";
  const label = decision?.semantic.label ?? "Worth a look";
  const company = opp.explanation?.company ?? new URL(opp.url).hostname.replace(/^www\./, "");
  const title = opp.explanation?.title ?? "Open role";
  const secondary = decision?.semantic.secondary;

  const tierColor =
    tier === "strong" ? "var(--success)" : tier === "low" ? "var(--text-muted)" : "var(--text-secondary)";

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-lg transition-all duration-200 border",
        selected
          ? "bg-[var(--surface-elevated)] border-[var(--accent)]"
          : "bg-transparent border-transparent hover:bg-[var(--surface)] hover:border-[var(--border)]"
      )}
    >
      {/* Score + Tier */}
      <div className="flex items-baseline gap-2 mb-1">
        <span
          className="font-mono text-sm font-semibold tabular-nums"
          style={{ color: "var(--text-primary)" }}
        >
          {career_score ?? 0}
        </span>
        <span className="text-xs font-medium" style={{ color: tierColor }}>
          {label}
        </span>
      </div>

      {/* Company + Title */}
      <div className="mb-1">
        <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          {company}
        </div>
        <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
          {title}
        </div>
      </div>

      {/* Secondary signal */}
      {secondary && (
        <div className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
          {secondary}
        </div>
      )}
    </button>
  );
}
