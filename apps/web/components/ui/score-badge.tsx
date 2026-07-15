import { cn } from "@/lib/utils";
import { MetricText } from "@/components/shared/metric-text";
import { LabelText } from "@/components/shared/label-text";
import { HelpCircle } from "lucide-react";

export type ScoreRecommendation = "APPLY" | "CONSIDER" | "SKIP";

interface ScoreBadgeProps {
  score: number;
  recommendation?: ScoreRecommendation;
  size?: "sm" | "md" | "lg";
  variant?: "rectangular" | "circular";
  showWhy?: boolean;
  onClickWhy?: () => void;
  className?: string;
}

const recColors: Record<ScoreRecommendation, string> = {
  APPLY:   "var(--success)",
  CONSIDER:"var(--accent)",
  SKIP:    "var(--text-muted)",
};

const ringHex: Record<ScoreRecommendation, string> = {
  APPLY:   "#7FB685",
  CONSIDER:"#FFB162",
  SKIP:    "#8D918F",
};

function getRec(score: number): ScoreRecommendation {
  if (score >= 70) return "APPLY";
  if (score >= 50) return "CONSIDER";
  return "SKIP";
}

const sizes = {
  sm: { dim: 64,  r: 28, sw: 3, textSize: "lg"  as const },
  md: { dim: 80,  r: 36, sw: 3, textSize: "xl"  as const },
  lg: { dim: 96,  r: 43, sw: 3, textSize: "xl"  as const },
};

export function ScoreBadge({
  score,
  recommendation,
  size = "md",
  variant = "rectangular",
  showWhy = false,
  onClickWhy,
  className,
}: ScoreBadgeProps) {
  const rec = recommendation ?? getRec(score);
  const s = sizes[size];

  if (variant === "circular") {
    const circ = 2 * Math.PI * s.r;
    const offset = circ - (score / 100) * circ;
    return (
      <div className={cn("relative inline-flex flex-col items-center gap-1", className)}>
        <div style={{ width: s.dim, height: s.dim, position: "relative" }}>
          <svg width={s.dim} height={s.dim} style={{ transform: "rotate(-90deg)" }}>
            <circle cx={s.dim / 2} cy={s.dim / 2} r={s.r} fill="none" stroke="var(--border)" strokeWidth={s.sw} />
            <circle
              cx={s.dim / 2} cy={s.dim / 2} r={s.r}
              fill="none"
              stroke={ringHex[rec]}
              strokeWidth={s.sw}
              strokeDasharray={circ}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: "stroke-dashoffset 0.5s ease-out" }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <MetricText value={score} size={s.textSize} />
          </div>
        </div>
        <LabelText style={{ color: recColors[rec] } as React.CSSProperties}>{rec}</LabelText>
      </div>
    );
  }

  return (
    <div
      className={cn("relative inline-flex flex-col items-center justify-center gap-1 rounded-lg border p-3", className)}
      style={{ background: "var(--surface)", borderColor: "var(--border)", width: s.dim, height: s.dim }}
    >
      <MetricText value={score} size={s.textSize} />
      <LabelText style={{ color: recColors[rec] } as React.CSSProperties}>{rec}</LabelText>
      {showWhy && onClickWhy && (
        <button
          onClick={onClickWhy}
          className="absolute top-1.5 right-1.5 h-5 w-5 rounded-md flex items-center justify-center transition-colors hover:bg-[var(--surface-hover)]"
          style={{ color: "var(--text-muted)" }}
          aria-label="Explain score"
        >
          <HelpCircle className="h-3 w-3" strokeWidth={2} />
        </button>
      )}
    </div>
  );
}
