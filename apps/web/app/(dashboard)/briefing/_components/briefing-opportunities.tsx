"use client";

import { SpotlightCard } from "@/components/patterns/spotlight-card";
import { SectionLabel } from "@/components/shared/narrative-section";
import { Movement } from "./movement";
import type { Opportunity } from "@/features/briefing/types";

export function BriefingOpportunities({ opportunities }: { opportunities: Opportunity[] }) {
  if (opportunities.length === 0) return null;
  return (
    <Movement delay={160}>
      <SectionLabel>Today&apos;s Opportunities</SectionLabel>
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2">
        {opportunities.map((opp, i) => (
          <div
            key={opp.id}
            className={i === 0 ? "md:pr-10 pb-8 md:pb-0" : "md:pl-10 pt-8 md:pt-0 md:border-l"}
            style={i === 0 ? undefined : { borderColor: "var(--border)" }}
          >
            <SpotlightCard
              company={opp.company}
              role={opp.role}
              location={opp.location}
              score={opp.score}
              recommendation={opp.recommendation}
              why={opp.why}
              gap={opp.gap}
              onApply={() => console.log(`[Opportunity] Apply — ${opp.company}`)}
              onGenerateResume={() => console.log(`[Opportunity] Generate resume — ${opp.company}`)}
              onWhy={() => console.log(`[Opportunity] Why ${opp.score} — ${opp.company}`)}
            />
          </div>
        ))}
      </div>
    </Movement>
  );
}
