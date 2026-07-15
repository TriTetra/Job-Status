"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { ArrowRight } from "lucide-react";

export interface DecisionItem {
  number: "01" | "02" | "03";
  action: string;
  reason: string;
  ctaLabel: string;
  ctaHref?: string;
  ctaOnClick?: () => void;
}

interface DecisionListProps {
  items: DecisionItem[];
  /** "stack" = vertical narrative; "columns" = borderless side-by-side typography */
  layout?: "stack" | "columns";
  className?: string;
}

export function DecisionList({ items, layout = "stack", className }: DecisionListProps) {
  const safeItems = items.slice(0, 3);
  const isColumns = layout === "columns";

  return (
    <div
      className={cn(
        "stagger",
        isColumns ? "grid grid-cols-1 md:grid-cols-3 gap-x-10 gap-y-8" : "space-y-6",
        className
      )}
    >
      {safeItems.map((item, idx) => (
        <div key={item.number} className="group flex flex-col">
          <div className="font-mono text-sm tabular-nums mb-2" style={{ color: "var(--accent)" }}>
            {item.number}
          </div>

          <NarrativeText size={isColumns ? "base" : "lg"} weight="semibold" className="mb-1">
            {item.action}
          </NarrativeText>

          <NarrativeText
            size={isColumns ? "sm" : "base"}
            className={cn("mb-3", isColumns && "flex-1")}
            style={{ color: "var(--text-secondary)" }}
          >
            {item.reason}
          </NarrativeText>

          {!isColumns && idx < safeItems.length - 1 && (
            <div className="h-px w-16 my-4" style={{ background: "var(--border)" }} />
          )}

          <button
            onClick={item.ctaOnClick}
            className={cn(
              "inline-flex items-center gap-1.5 text-sm transition-colors duration-150 opacity-80 group-hover:opacity-100 focus-visible:outline-none rounded",
              isColumns && "mt-auto self-start"
            )}
            style={{ color: "var(--accent)" }}
          >
            <span>{item.ctaLabel}</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform duration-150 group-hover:translate-x-0.5" strokeWidth={2} />
          </button>
        </div>
      ))}
    </div>
  );
}
