"use client";

import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { Zap } from "lucide-react";

interface BriefingEmptyProps {
  watching: string[];
}

export function BriefingEmpty({ watching }: BriefingEmptyProps) {
  return (
    <div className="narrative-container px-6 lg:px-8 py-16">
      <NarrativeText size="3xl" weight="semibold" className="rhythm-pause block">
        Good evening.
      </NarrativeText>

      <div className="rhythm-breathing space-y-[var(--rhythm-thought)]">
        <NarrativeText size="lg">Your briefing is quiet today.</NarrativeText>
        <NarrativeText size="lg" style={{ color: "var(--text-secondary)" }}>
          Nothing urgent in your career landscape. That&apos;s often a good sign.
        </NarrativeText>
      </div>

      <div className="rhythm-breathing">
        <div
          className="text-[11px] uppercase tracking-[0.08em] mb-4"
          style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
        >
          We&apos;re Watching
        </div>
        <div className="space-y-2.5">
          {watching.map((item, i) => (
            <div key={i} className="flex items-start gap-3 text-base" style={{ color: "var(--text-secondary)" }}>
              <span className="shrink-0 mt-1.5" style={{ color: "var(--accent)" }}>•</span>
              <span className="leading-relaxed">{item}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rhythm-decision">
        <NarrativeText size="base" className="mb-4 block" style={{ color: "var(--text-muted)" }}>
          Want to expand the search?
        </NarrativeText>
        <Button variant="outline" onClick={() => console.log("[Briefing Empty] Scan for new opportunities")}>
          <Zap className="h-4 w-4" strokeWidth={1.75} />
          Scan for new opportunities
        </Button>
      </div>

      <div className="rhythm-reflection space-y-[var(--rhythm-thought)]">
        <NarrativeText size="lg" style={{ color: "var(--text-muted)" }}>
          We&apos;ll let you know when something worth your attention appears.
        </NarrativeText>
        <NarrativeText size="lg" style={{ color: "var(--text-muted)" }}>
          See you tomorrow.
        </NarrativeText>
      </div>
    </div>
  );
}
