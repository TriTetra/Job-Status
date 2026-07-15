"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { useState } from "react";

export type FocusPriority = "high" | "medium" | "low";

interface TodaysFocusItemProps {
  action: string;
  context: string;
  whyLabel?: string;
  priority?: FocusPriority;
  onWhyClick?: () => void;
  onComplete?: () => void;
  className?: string;
}

const priorityBorder: Record<FocusPriority, string> = {
  high:   "var(--accent)",
  medium: "var(--border-strong)",
  low:    "var(--border)",
};

export function TodaysFocusItem({
  action,
  context,
  whyLabel = "Why?",
  priority = "medium",
  onWhyClick,
  onComplete,
  className,
}: TodaysFocusItemProps) {
  const [completed, setCompleted] = useState(false);

  const handleCheck = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCompleted((v) => !v);
    onComplete?.();
  };

  return (
    <div
      className={cn(
        "group flex items-start gap-4 px-6 py-5 transition-colors border-l-2",
        completed ? "opacity-60" : "hover:bg-[var(--surface-hover)]",
        className
      )}
      style={{ borderLeftColor: priorityBorder[priority] }}
    >
      <button
        onClick={handleCheck}
        className={cn(
          "h-5 w-5 rounded-full border-2 shrink-0 mt-0.5 transition-all flex items-center justify-center"
        )}
        style={
          completed
            ? { background: "var(--accent)", borderColor: "var(--accent)" }
            : { borderColor: "var(--border-strong)" }
        }
        aria-label={completed ? "Mark incomplete" : "Mark complete"}
      >
        {completed && <Check className="h-3 w-3" style={{ color: "var(--accent-fg)" }} strokeWidth={3} />}
      </button>

      <div className="flex-1 min-w-0">
        <p
          className={cn("text-sm font-medium leading-snug", completed && "line-through")}
          style={{ color: completed ? "var(--text-muted)" : "var(--text-primary)" }}
        >
          {action}
        </p>
        <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          {context}
        </div>
      </div>

      {onWhyClick && !completed && (
        <button
          onClick={(e) => { e.stopPropagation(); onWhyClick(); }}
          className="text-xs opacity-0 group-hover:opacity-100 transition-opacity shrink-0 self-center"
          style={{ color: "var(--accent)" }}
        >
          {whyLabel} →
        </button>
      )}
    </div>
  );
}

export function TodaysFocusList({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn("rounded-lg overflow-hidden", className)}
      style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
    >
      {children}
    </div>
  );
}
