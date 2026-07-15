import { cn } from "@/lib/utils";

type NarrativeVariant = "default" | "highlight" | "warning" | "success" | "muted";

const variants: Record<NarrativeVariant, string> = {
  default:   "text-[var(--text-primary)]",
  highlight: "text-[var(--accent-warm)]",
  warning:   "text-[var(--warning)]",
  success:   "text-[var(--success)]",
  muted:     "text-[var(--text-muted)]",
};

interface NarrativeLineProps {
  children: React.ReactNode;
  variant?: NarrativeVariant;
  className?: string;
}

export function NarrativeLine({ children, variant = "default", className }: NarrativeLineProps) {
  return (
    <p className={cn("text-base leading-relaxed", variants[variant], className)}>
      {children}
    </p>
  );
}

interface NarrativeBlockProps {
  greeting?: string;
  children: React.ReactNode;
  className?: string;
}

export function NarrativeBlock({ greeting, children, className }: NarrativeBlockProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {greeting && (
        <p className="text-xs uppercase tracking-widest text-[var(--text-muted)] mb-3">
          {greeting}
        </p>
      )}
      {children}
    </div>
  );
}
