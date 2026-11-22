"use client";

import { cn, formatScore } from "@/lib/utils";
import { tierOf } from "@/features/opportunities/tier";
import {
  CHANCE_COLOR, CHANCE_LABEL, DECISION_LABEL, TIER_COLOR,
  chanceOf, companyOf, postedAgo, salaryOf, whereOf,
} from "@/features/opportunities/format";
import type { Opportunity } from "@/features/opportunities/types";

interface OpportunityCardCompactProps {
  opp: Opportunity;
  selected: boolean;
  onClick: () => void;
}

/**
 * One row of the scanner: company + score, the role, then where / pay / age / chance.
 * Borderless; the selected row gets an accent rule and a surface.
 */
export function OpportunityCardCompact({ opp, selected, onClick }: OpportunityCardCompactProps) {
  const tier = tierOf(opp);
  const chance = chanceOf(opp);
  const age = postedAgo(opp);
  const facts = [whereOf(opp), salaryOf(opp), age].filter(Boolean).join(" · ");
  const status = DECISION_LABEL[opp.user_decision?.status ?? "unreviewed"];

  return (
    <button
      onClick={onClick}
      aria-current={selected ? "true" : undefined}
      className={cn(
        "relative w-full text-left px-4 py-3.5 rounded-md transition-colors",
        selected ? "bg-[var(--surface)]" : "hover:bg-[var(--surface)]/60",
      )}
    >
      {selected && <span className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" style={{ background: "var(--accent)" }} />}
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{companyOf(opp)}</span>
        <span className="font-mono text-sm font-semibold tabular-nums shrink-0" style={{ color: TIER_COLOR[tier] }}>
          {formatScore(opp.career_score)}
        </span>
      </div>
      <div className="text-sm mt-0.5 line-clamp-2" style={{ color: "var(--text-secondary)" }}>
        {opp.explanation?.title ?? "Open role"}
      </div>
      <div className="mt-1.5 flex items-baseline justify-between gap-3 text-xs">
        <span className="truncate" style={{ color: "var(--text-muted)" }}>{facts}</span>
        <span className="shrink-0" style={{ color: status ? "var(--accent)" : CHANCE_COLOR[chance] }}>
          {status ?? CHANCE_LABEL[chance]}
        </span>
      </div>
    </button>
  );
}
