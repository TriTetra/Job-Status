"use client";

import { useRouter } from "next/navigation";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { Zap, TrendingUp, Sparkles } from "lucide-react";

interface BriefingEmptyProps {
  watching: string[];
  stats?: {
    skills_count?: number;
    projects_count?: number;
    achievements_count?: number;
    companies_count?: number;
  };
  greeting?: string;
}

export function BriefingEmpty({ watching, stats, greeting = "Good evening" }: BriefingEmptyProps) {
  const router = useRouter();

  const hasEvidence = (stats?.skills_count ?? 0) > 0 || (stats?.projects_count ?? 0) > 0;
  const hasCompanies = watching.some((item) => item.includes("hiring trend"));

  return (
    <div className="narrative-container px-6 lg:px-8 py-16">
      <NarrativeText size="3xl" weight="semibold" className="rhythm-pause block">
        {greeting}.
      </NarrativeText>

      <div className="rhythm-breathing space-y-[var(--rhythm-thought)]">
        <NarrativeText size="lg">Your briefing is quiet today.</NarrativeText>
        <NarrativeText size="lg" style={{ color: "var(--text-secondary)" }}>
          {hasEvidence
            ? "Your career graph is building, but we haven't found matching opportunities yet."
            : "Nothing urgent in your career landscape. That's often a good sign."}
        </NarrativeText>
      </div>

      {/* Stats summary — only show if we have evidence */}
      {hasEvidence && (
        <div className="rhythm-section">
          <div
            className="text-[11px] uppercase tracking-[0.08em] mb-4"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
          >
            Your Career Graph
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(stats?.skills_count ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "var(--surface)" }}>
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(127,182,133,0.12)" }}
                >
                  <Sparkles className="h-4 w-4" style={{ color: "var(--success)" }} strokeWidth={2} />
                </div>
                <div>
                  <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                    {stats?.skills_count}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Skills
                  </div>
                </div>
              </div>
            )}
            {(stats?.projects_count ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "var(--surface)" }}>
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(255,177,98,0.12)" }}
                >
                  <Sparkles className="h-4 w-4" style={{ color: "var(--accent)" }} strokeWidth={2} />
                </div>
                <div>
                  <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                    {stats?.projects_count}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Projects
                  </div>
                </div>
              </div>
            )}
            {(stats?.achievements_count ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "var(--surface)" }}>
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(255,177,98,0.12)" }}
                >
                  <Sparkles className="h-4 w-4" style={{ color: "var(--warning, #e6a817)" }} strokeWidth={2} />
                </div>
                <div>
                  <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                    {stats?.achievements_count}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Honors
                  </div>
                </div>
              </div>
            )}
            {(stats?.companies_count ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "var(--surface)" }}>
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(107,165,212,0.12)" }}
                >
                  <TrendingUp className="h-4 w-4" style={{ color: "var(--info)" }} strokeWidth={2} />
                </div>
                <div>
                  <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                    {stats?.companies_count}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Experiences
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Watching list */}
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
              <span className="shrink-0 mt-1.5" style={{ color: "var(--accent)" }}>
                •
              </span>
              <span className="leading-relaxed">{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="rhythm-decision">
        <NarrativeText size="base" className="mb-4 block" style={{ color: "var(--text-muted)" }}>
          {hasCompanies
            ? "Companies are hiring — let's find roles that match your profile."
            : hasEvidence
              ? "Your skills are mapped — ready to match against live roles."
              : "Want to expand the search?"}
        </NarrativeText>
        <Button variant="outline" onClick={() => router.push("/inbox")}>
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
