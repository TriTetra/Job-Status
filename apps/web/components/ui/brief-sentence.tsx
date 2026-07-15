import { cn } from "@/lib/utils";
import { type ReactNode } from "react";
import { ArrowRight } from "lucide-react";

export type BriefSentenceTone =
  | "neutral"
  | "highlight"
  | "positive"
  | "negative"
  | "warning"
  | "opportunity";

interface BriefSentenceProps {
  children: ReactNode;
  tone?: BriefSentenceTone;
  icon?: ReactNode;
  action?: { label: string; onClick?: () => void };
  className?: string;
}

const toneColors: Record<BriefSentenceTone, string> = {
  neutral:     "var(--text-secondary)",
  highlight:   "var(--accent)",
  positive:    "var(--success)",
  negative:    "var(--danger)",
  warning:     "var(--warning)",
  opportunity: "var(--info)",
};

export function BriefSentence({
  children,
  tone = "neutral",
  icon,
  action,
  className,
}: BriefSentenceProps) {
  return (
    <div className={cn("flex items-start gap-3 group", className)}>
      {icon && (
        <div className="mt-0.5 shrink-0" style={{ color: toneColors[tone] }}>
          {icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-lg leading-relaxed" style={{ color: toneColors[tone] }}>
          {children}
        </p>
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="shrink-0 inline-flex items-center gap-1 text-sm transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 mt-1"
          style={{ color: "var(--accent)" }}
        >
          {action.label}
          <ArrowRight className="h-3.5 w-3.5" strokeWidth={2} />
        </button>
      )}
    </div>
  );
}

export function BriefHighlight({
  children,
  variant = "default",
}: {
  children: ReactNode;
  variant?: "default" | "accent" | "positive" | "negative";
}) {
  const colors = {
    default:  "var(--text-primary)",
    accent:   "var(--accent)",
    positive: "var(--success)",
    negative: "var(--danger)",
  };
  return (
    <span className="font-medium" style={{ color: colors[variant] }}>
      {children}
    </span>
  );
}
