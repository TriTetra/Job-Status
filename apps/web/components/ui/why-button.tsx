"use client";

import { useState } from "react";
import { HelpCircle } from "lucide-react";
import { WhyPanel, type BreakdownItem } from "./why-panel";

interface WhyButtonProps {
  title: string;
  score?: number;
  breakdown: BreakdownItem[];
  baseScore?: number;
  compact?: boolean;
  className?: string;
}

export function WhyButton({
  title,
  score,
  breakdown,
  baseScore = 50,
  compact = false,
  className,
}: WhyButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={
          compact
            ? "inline-flex items-center gap-1 text-xs transition-colors"
            : "inline-flex items-center gap-1.5 px-2.5 h-7 rounded-md text-xs font-medium border transition-colors"
        }
        style={
          compact
            ? { color: "var(--accent)" }
            : {
                color: "var(--accent)",
                borderColor: "rgba(255,177,98,0.3)",
              }
        }
        onMouseEnter={(e) => {
          if (!compact) e.currentTarget.style.background = "rgba(255,177,98,0.1)";
        }}
        onMouseLeave={(e) => {
          if (!compact) e.currentTarget.style.background = "transparent";
        }}
      >
        <HelpCircle className="h-3 w-3" strokeWidth={2} />
        {compact ? "Why?" : "Why this score?"}
      </button>

      <WhyPanel
        isOpen={open}
        onClose={() => setOpen(false)}
        title={title}
        score={score}
        breakdown={breakdown}
        baseScore={baseScore}
      />
    </>
  );
}
