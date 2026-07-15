import { cn } from "@/lib/utils";
import { MetricText } from "@/components/shared/metric-text";

export interface SkillTrend {
  skill: string;
  change: number;
  direction: "up" | "down" | "stable";
  mentions?: number;
}

interface MarketPulseProps {
  trends: SkillTrend[];
  onViewFullReport?: () => void;
  className?: string;
}

function TrendCard({ trend }: { trend: SkillTrend }) {
  const isStable = trend.direction === "stable";
  const displayValue = isStable
    ? "stable"
    : `${trend.change > 0 ? "+" : ""}${trend.change}`;

  return (
    <div
      className="rounded-lg p-4 transition-colors hover:bg-[var(--surface-hover)] cursor-pointer"
      style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
          {trend.skill}
        </span>
        {trend.mentions !== undefined && (
          <span className="text-[11px] tabular-nums" style={{ color: "var(--text-muted)" }}>
            {trend.mentions}
          </span>
        )}
      </div>
      <MetricText
        value={displayValue}
        unit={isStable ? undefined : "%"}
        size="lg"
        trend={trend.direction}
        showTrendIcon={!isStable}
      />
    </div>
  );
}

export function MarketPulse({ trends, onViewFullReport, className }: MarketPulseProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {trends.map((t) => (
          <TrendCard key={t.skill} trend={t} />
        ))}
      </div>
      {onViewFullReport && (
        <button
          onClick={onViewFullReport}
          className="w-full text-center text-sm py-2 transition-colors"
          style={{ color: "var(--accent)" }}
        >
          Full market report →
        </button>
      )}
    </div>
  );
}
