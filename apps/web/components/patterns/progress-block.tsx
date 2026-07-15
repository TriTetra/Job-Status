"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { ArrowRight } from "lucide-react";

export interface ProgressBlockProps {
  headline: string;
  attribution: string;
  promise: string;
  ctaLabel?: string;
  ctaHref?: string;
  ctaOnClick?: () => void;
  className?: string;
}

export function ProgressBlock({
  headline,
  attribution,
  promise,
  ctaLabel,
  ctaOnClick,
  className,
}: ProgressBlockProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <NarrativeText size="lg" weight="semibold">
        {headline}
      </NarrativeText>

      <NarrativeText size="base" style={{ color: "var(--text-secondary)" } as React.CSSProperties}>
        {attribution}
      </NarrativeText>

      <NarrativeText size="base" style={{ color: "var(--text-muted)" } as React.CSSProperties}>
        {promise}
      </NarrativeText>

      {ctaLabel && (
        <button
          onClick={ctaOnClick}
          className="group inline-flex items-center gap-1.5 text-sm transition-colors duration-150 pt-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded"
          style={{ color: "var(--accent)" }}
        >
          <span>{ctaLabel}</span>
          <ArrowRight className="h-3.5 w-3.5 transition-transform duration-150 group-hover:translate-x-0.5" strokeWidth={2} />
        </button>
      )}
    </div>
  );
}
