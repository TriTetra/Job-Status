import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

export type RhythmSpacing =
  | "pause"
  | "thought"
  | "section"
  | "decision"
  | "reflection"
  | "breathing"
  | "none";

interface NarrativeSectionProps {
  children: ReactNode;
  spacingAfter?: RhythmSpacing;
  sectionId?: string;
  className?: string;
  as?: "section" | "div" | "article";
}

const spacingClasses: Record<RhythmSpacing, string> = {
  pause:      "rhythm-pause",
  thought:    "rhythm-thought",
  section:    "rhythm-section",
  decision:   "rhythm-decision",
  reflection: "rhythm-reflection",
  breathing:  "rhythm-breathing",
  none:       "",
};

export function NarrativeSection({
  children,
  spacingAfter = "none",
  sectionId,
  className,
  as: Component = "section",
}: NarrativeSectionProps) {
  return (
    <Component
      data-section-id={sectionId}
      className={cn(spacingClasses[spacingAfter], className)}
    >
      {children}
    </Component>
  );
}

export function SectionLabel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("text-[11px] uppercase tracking-[0.08em] mb-8", className)}
      style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </div>
  );
}
