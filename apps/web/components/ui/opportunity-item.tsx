"use client";

import { cn } from "@/lib/utils";
import { ScoreBadge } from "./score-badge";
import { StatusPill } from "./status-pill";
import { SkillTag } from "./skill-tag";
import { Button } from "@/components/shared/button";
import { WhyButton } from "./why-button";
import { type BreakdownItem } from "./why-panel";
import { MapPin, Clock, Briefcase } from "lucide-react";
import { LabelText } from "@/components/shared/label-text";

export type { BreakdownItem };

export interface OpportunityItemProps {
  score: number;
  recommendation: "APPLY" | "CONSIDER" | "SKIP";
  company: { name: string; tier?: string };
  role: string;
  location: string;
  remote?: boolean;
  visaSponsorship?: boolean;
  deadline?: string;
  matchedSkills: { name: string; confidence?: number }[];
  gapSkills: string[];
  whyHighlights: string[];
  breakdown: BreakdownItem[];
  onApply?: () => void;
  onGenerateResume?: () => void;
  onViewCompany?: () => void;
  className?: string;
}

export function OpportunityItem({
  score,
  recommendation,
  company,
  role,
  location,
  remote = false,
  visaSponsorship = false,
  deadline,
  matchedSkills,
  gapSkills,
  whyHighlights,
  breakdown,
  onApply,
  onGenerateResume,
  onViewCompany,
  className,
}: OpportunityItemProps) {
  return (
    <article
      className={cn("rounded-lg p-6 transition-colors hover:bg-[var(--surface-hover)]", className)}
      style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
    >
      {/* Header */}
      <div className="flex items-start gap-4 mb-5">
        <ScoreBadge score={score} recommendation={recommendation} size="md" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              {company.name}
            </span>
            {company.tier && <StatusPill label={company.tier} variant="neutral" size="sm" />}
            {visaSponsorship && <StatusPill label="H1B ✓" variant="success" size="sm" />}
          </div>
          <span className="text-base" style={{ color: "var(--text-secondary)" }}>{role}</span>
          <div className="flex items-center gap-3 mt-2 text-sm flex-wrap" style={{ color: "var(--text-muted)" }}>
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" strokeWidth={1.75} />{location}
            </span>
            {remote && (
              <span className="inline-flex items-center gap-1" style={{ color: "var(--accent)" }}>
                <Briefcase className="h-3.5 w-3.5" strokeWidth={1.75} />Remote
              </span>
            )}
            {deadline && (
              <span className="inline-flex items-center gap-1" style={{ color: "var(--warning)" }}>
                <Clock className="h-3.5 w-3.5" strokeWidth={1.75} />{deadline}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Why highlights */}
      {whyHighlights.length > 0 && (
        <div className="mb-4">
          <LabelText className="mb-2 block">Why this match</LabelText>
          <div className="space-y-1">
            {whyHighlights.map((h, i) => (
              <div key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--text-secondary)" }}>
                <span className="shrink-0" style={{ color: "var(--success)" }}>✓</span>
                <span>{h}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matched skills */}
      {matchedSkills.length > 0 && (
        <div className="mb-4">
          <LabelText className="mb-2 block">Matched skills</LabelText>
          <div className="flex flex-wrap gap-2">
            {matchedSkills.map((s) => (
              <SkillTag key={s.name} name={s.name} confidence={s.confidence} variant="matched" />
            ))}
          </div>
        </div>
      )}

      {/* Gaps */}
      {gapSkills.length > 0 && (
        <div className="mb-5">
          <LabelText className="mb-2 block">Gaps</LabelText>
          <div className="flex flex-wrap gap-2">
            {gapSkills.map((s) => (
              <SkillTag key={s} name={s} variant="gap" />
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div
        className="flex items-center gap-2 pt-4 border-t flex-wrap"
        style={{ borderColor: "var(--border)" }}
      >
        <Button variant="primary" size="sm" onClick={onApply}>Apply</Button>
        <Button variant="secondary" size="sm" onClick={onGenerateResume}>Generate resume</Button>
        <Button variant="outline" size="sm" onClick={onViewCompany}>View company</Button>
        <div className="ml-auto">
          <WhyButton title={`Why ${score}?`} score={score} baseScore={50} breakdown={breakdown} compact />
        </div>
      </div>
    </article>
  );
}

export function OpportunityFeed({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("space-y-3", className)}>{children}</div>;
}
