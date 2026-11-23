"use client";

import { cn, formatScore } from "@/lib/utils";
import { CompanyLogo } from "@/components/shared/company-logo";
import { PlaceBadge } from "./place-badge";
import { AdzunaBadge, isAdzuna } from "./adzuna-badge";
import { feedLabel } from "@/features/opportunities/feeds";
import { tierOf } from "@/features/opportunities/tier";
import {
  CHANCE_COLOR, CHANCE_LABEL, DECISION_LABEL, TIER_COLOR,
  chanceOf, companyOf, postedAgo, salaryOf, trustTag,
} from "@/features/opportunities/format";
import type { Opportunity } from "@/features/opportunities/types";

interface OpportunityCardCompactProps {
  opp: Opportunity;
  selected: boolean;
  onClick: () => void;
}

/** One row of the scanner: logo, role, company, where / pay, then score + chance. */
export function OpportunityCardCompact({ opp, selected, onClick }: OpportunityCardCompactProps) {
  const tier = tierOf(opp);
  const chance = chanceOf(opp);
  const company = companyOf(opp);
  const salary = salaryOf(opp);
  const status = DECISION_LABEL[opp.user_decision?.status ?? "unreviewed"];
  const age = postedAgo(opp);
  const via = feedLabel(opp.explanation?.source);
  const tag = trustTag(opp);
  const key = typeof opp.explanation?.company_key === "string" ? opp.explanation.company_key : null;

  const adzuna = isAdzuna(opp.explanation?.source);
  return (
    <div className="relative">
    <button
      onClick={onClick}
      aria-current={selected ? "true" : undefined}
      className={cn(
        "relative w-full text-left grid grid-cols-[2.5rem_minmax(0,1fr)_auto] gap-x-3 px-3 py-3 rounded-lg transition-colors",
        adzuna && "pb-10",
        selected ? "bg-[var(--surface)]" : "hover:bg-[rgba(44,59,77,0.5)]",
      )}
    >
      {selected && <span className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" style={{ background: "var(--accent)" }} />}
      <CompanyLogo name={company} companyKey={key} jobUrl={opp.url} size={40} className="mt-0.5" />
      <div className="min-w-0">
        <p className="text-sm font-medium leading-snug line-clamp-2" style={{ color: "var(--text-primary)" }}>
          {opp.explanation?.title ?? "Open role"}
        </p>
        <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
          {company}{age ? <span style={{ color: "var(--text-muted)" }}> · {age}</span> : null}
          {via ? <span style={{ color: "var(--text-muted)" }}> · via {via}</span> : null}
          {tag ? <span style={{ color: tag.color }}> · {tag.text}</span> : null}
        </p>
        <p className="text-xs mt-1 flex items-center gap-2 min-w-0" style={{ color: "var(--text-muted)" }}>
          <PlaceBadge ex={opp.explanation ?? {}} compact className="min-w-0" />
          {salary && <span className="shrink-0">· {salary}</span>}
        </p>
      </div>
      <div className="text-right">
        <p className="font-mono text-base font-semibold tabular-nums leading-none" style={{ color: TIER_COLOR[tier] }}>
          {formatScore(opp.career_score)}
        </p>
        <p className="text-[10px] mt-1.5 whitespace-nowrap" style={{ color: status ? "var(--accent)" : CHANCE_COLOR[chance] }}>
          {status ?? CHANCE_LABEL[chance]}
        </p>
      </div>
    </button>
    {/* Adzuna's terms: each Adzuna listing carries their label, linked to them (outside the button) */}
    {adzuna && <AdzunaBadge country={opp.explanation?.countries?.[0]} className="absolute left-[4.25rem] bottom-2.5" />}
    </div>
  );
}
