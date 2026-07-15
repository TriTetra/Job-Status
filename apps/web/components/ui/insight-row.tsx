import { cn } from "@/lib/utils";
import { Lightbulb, TrendingUp, TrendingDown, Sparkles } from "lucide-react";
import { type ReactNode } from "react";
import { MetricText } from "@/components/shared/metric-text";

export type InsightType = "tip" | "trend" | "achievement" | "warning";

interface InsightRowProps {
  type?: InsightType;
  icon?: ReactNode;
  title: string;
  description: string;
  metric?: { value: string; trend?: "up" | "down" | "stable" };
  confidence?: number;
  action?: { label: string; onClick?: () => void };
  className?: string;
}

const typeConfig: Record<InsightType, { Icon: React.ComponentType<{ className?: string; strokeWidth?: number; style?: React.CSSProperties }>; color: string; bg: string }> = {
  tip:         { Icon: Lightbulb,   color: "var(--accent)",   bg: "rgba(255,177,98,0.1)"  },
  trend:       { Icon: TrendingUp,  color: "var(--success)",  bg: "rgba(127,182,133,0.1)" },
  achievement: { Icon: Sparkles,    color: "var(--accent)",   bg: "rgba(255,177,98,0.1)"  },
  warning:     { Icon: TrendingDown, color: "var(--warning)", bg: "rgba(255,177,98,0.1)"  },
};

export function InsightRow({
  type = "tip",
  icon,
  title,
  description,
  metric,
  confidence,
  action,
  className,
}: InsightRowProps) {
  const { Icon, color, bg } = typeConfig[type];

  return (
    <div
      className={cn("flex items-start gap-4 rounded-lg p-5", className)}
      style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
    >
      <div
        className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0"
        style={{ background: bg }}
      >
        {icon ?? <Icon className="h-[18px] w-[18px]" style={{ color } as React.CSSProperties} strokeWidth={1.75} />}
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>
          {title}
        </div>
        <div className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {description}
        </div>
        {confidence !== undefined && (
          <div className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
            Confidence:{" "}
            <MetricText value={confidence} unit="%" size="sm" showTrendIcon={false} />
          </div>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-2.5 inline-flex items-center gap-1 text-xs transition-colors"
            style={{ color: "var(--accent)" }}
          >
            {action.label} →
          </button>
        )}
      </div>

      {metric && (
        <div className="shrink-0">
          <MetricText value={metric.value} size="lg" trend={metric.trend} />
        </div>
      )}
    </div>
  );
}
