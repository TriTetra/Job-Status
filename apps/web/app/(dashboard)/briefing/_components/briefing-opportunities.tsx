"use client";

import { useState } from "react";
import { SpotlightCard } from "@/components/patterns/spotlight-card";
import { SectionLabel } from "@/components/shared/narrative-section";
import { opportunitiesApi } from "@/features/opportunities/api";
import { Movement } from "./movement";
import type { Opportunity } from "@/features/briefing/types";

type ShortlistState = "saving" | "done" | "error";
const LABEL: Record<ShortlistState, string> = { saving: "Saving…", done: "Shortlisted ✓", error: "Didn't save — retry" };

export function BriefingOpportunities({ opportunities }: { opportunities: Opportunity[] }) {
  const [shortlist, setShortlist] = useState<Record<string, ShortlistState>>({});
  if (opportunities.length === 0) return null;

  const save = async (id: string) => {
    if (shortlist[id] === "saving" || shortlist[id] === "done") return;
    setShortlist((s) => ({ ...s, [id]: "saving" }));
    try {
      await opportunitiesApi.decide(id, "to_apply");
      setShortlist((s) => ({ ...s, [id]: "done" }));
    } catch {
      setShortlist((s) => ({ ...s, [id]: "error" }));
    }
  };

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
              postingUrl={opp.postingUrl}
              whyHref={opp.whyHref}
              onShortlist={() => save(opp.id)}
              shortlistLabel={shortlist[opp.id] ? LABEL[shortlist[opp.id]] : "Shortlist"}
            />
          </div>
        ))}
      </div>
    </Movement>
  );
}
