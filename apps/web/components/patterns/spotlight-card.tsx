"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import Link from "next/link";
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
  /** The company's own posting; opens in a new tab */
  postingUrl?: string;
  /** Where "Why {score}?" leads (the opportunity in the inbox) */
  whyHref?: string;
  onShortlist?: () => void;
  /** "Shortlist" · "Saving…" · "Shortlisted ✓" · an error */
  shortlistLabel?: string;
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
  postingUrl,
  whyHref,
  onShortlist,
  shortlistLabel = "Shortlist",
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
      {why.length > 0 && (
        <NarrativeText size="sm" className="mb-1" style={{ color: "var(--text-secondary)" }}>
          Strong on {why.join(" and ")}.
        </NarrativeText>
      )}
      {gap && (
        <NarrativeText size="sm" className="mb-4" style={{ color: "var(--text-muted)" }}>
          Gap: {gap}.
        </NarrativeText>
      )}

      {/* Actions as text links, not buttons */}
      <div className="flex items-center gap-5 text-sm mt-auto">
        {postingUrl && (
          <a
            href={postingUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-medium transition-colors group/apply"
            style={{ color: "var(--accent)" }}
          >
            Open posting
            <ArrowRight className="h-3.5 w-3.5 transition-transform duration-150 group-hover/apply:translate-x-0.5" strokeWidth={2} />
          </a>
        )}
        {onShortlist && (
          <button onClick={onShortlist} className="transition-colors" style={{ color: "var(--text-secondary)" }}>
            {shortlistLabel}
          </button>
        )}
        {whyHref && (
          <Link href={whyHref} className="ml-auto transition-colors" style={{ color: "var(--text-muted)" }}>
            Why {score}?
          </Link>
        )}
      </div>
    </article>
  );
}
