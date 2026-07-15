import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

export type NarrativeTone =
  | "neutral"
  | "highlight"
  | "positive"
  | "negative"
  | "warning"
  | "opportunity";

export type NarrativeSize = "sm" | "base" | "lg" | "xl" | "2xl" | "3xl";
export type NarrativeWeight = "normal" | "medium" | "semibold";

interface NarrativeTextProps {
  children: ReactNode;
  tone?: NarrativeTone;
  size?: NarrativeSize;
  weight?: NarrativeWeight;
  className?: string;
  style?: React.CSSProperties;
  as?: "p" | "span" | "div" | "h1" | "h2" | "h3";
}

const toneStyles: Record<NarrativeTone, string> = {
  neutral:     "text-[var(--text-primary)]",
  highlight:   "text-[var(--accent)]",
  positive:    "text-[var(--success)]",
  negative:    "text-[var(--danger)]",
  warning:     "text-[var(--warning)]",
  opportunity: "text-[var(--info)]",
};

const sizeStyles: Record<NarrativeSize, string> = {
  sm:   "text-sm",
  base: "text-base",
  lg:   "text-lg",
  xl:   "text-xl",
  "2xl": "text-2xl",
  "3xl": "text-3xl",
};

const weightStyles: Record<NarrativeWeight, string> = {
  normal:   "font-normal",
  medium:   "font-medium",
  semibold: "font-semibold",
};

export function NarrativeText({
  children,
  tone = "neutral",
  size = "base",
  weight = "normal",
  className,
  style,
  as: Component = "p",
}: NarrativeTextProps) {
  return (
    <Component
      className={cn(
        "leading-relaxed",
        toneStyles[tone],
        sizeStyles[size],
        weightStyles[weight],
        className
      )}
      style={style}
    >
      {children}
    </Component>
  );
}
