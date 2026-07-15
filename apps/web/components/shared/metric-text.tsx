import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export type MetricSize = "sm" | "md" | "lg" | "xl" | "2xl";
export type MetricTrend = "up" | "down" | "stable";

interface MetricTextProps {
  value: number | string;
  unit?: string;
  size?: MetricSize;
  trend?: MetricTrend;
  prefix?: string;
  showTrendIcon?: boolean;
  className?: string;
}

const sizeStyles: Record<MetricSize, string> = {
  sm:  "text-sm",
  md:  "text-base",
  lg:  "text-lg",
  xl:  "text-2xl",
  "2xl": "text-4xl",
};

const trendColors: Record<MetricTrend, string> = {
  up:     "text-[var(--success)]",
  down:   "text-[var(--danger)]",
  stable: "text-[var(--text-muted)]",
};

function TrendIcon({ trend }: { trend: MetricTrend }) {
  const icons = { up: TrendingUp, down: TrendingDown, stable: Minus };
  const Icon = icons[trend];
  return <Icon className="inline-block w-4 h-4 ml-1" />;
}

export function MetricText({
  value,
  unit,
  size = "md",
  trend,
  prefix,
  showTrendIcon = true,
  className,
}: MetricTextProps) {
  return (
    <span
      className={cn(
        "font-mono font-semibold tabular-nums tracking-tight",
        trend ? trendColors[trend] : "text-[var(--text-primary)]",
        sizeStyles[size],
        className
      )}
    >
      {prefix}
      {value}
      {unit && (
        <span className="text-[var(--text-secondary)] ml-0.5">{unit}</span>
      )}
      {trend && showTrendIcon && <TrendIcon trend={trend} />}
    </span>
  );
}
