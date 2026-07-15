import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  subVariant?: "accent" | "warning" | "success" | "muted";
  className?: string;
}

const subColors = {
  accent:  "text-[var(--accent)]",
  warning: "text-[var(--warning)]",
  success: "text-[var(--success)]",
  muted:   "text-[var(--text-muted)]",
};

export function MetricCard({ label, value, sub, subVariant = "muted", className }: MetricCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg bg-[var(--surface)] border border-[var(--border)] px-4 py-3",
        className
      )}
    >
      <p className="text-xs text-[var(--text-muted)] mb-1">{label}</p>
      <p className="text-2xl font-medium text-[var(--text-primary)] tabular-nums">{value}</p>
      {sub && (
        <p className={cn("text-xs mt-1", subColors[subVariant])}>{sub}</p>
      )}
    </div>
  );
}
