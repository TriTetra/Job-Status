import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

export type StatusVariant =
  | "success"
  | "warning"
  | "danger"
  | "neutral"
  | "accent"
  | "info";

interface StatusPillProps {
  label: string;
  variant?: StatusVariant;
  icon?: ReactNode;
  dot?: boolean;
  size?: "sm" | "md";
  className?: string;
}

const variantStyles: Record<StatusVariant, { bg: string; text: string; border: string; dot: string }> = {
  success: { bg: "rgba(127,182,133,0.1)", text: "var(--success)",  border: "rgba(127,182,133,0.25)", dot: "var(--success)"  },
  warning: { bg: "rgba(255,177,98,0.1)",  text: "var(--warning)",  border: "rgba(255,177,98,0.25)",  dot: "var(--warning)"  },
  danger:  { bg: "rgba(201,106,90,0.1)",  text: "var(--danger)",   border: "rgba(201,106,90,0.25)",  dot: "var(--danger)"   },
  neutral: { bg: "var(--surface-hover)",  text: "var(--text-secondary)", border: "var(--border)",    dot: "var(--text-muted)"},
  accent:  { bg: "rgba(255,177,98,0.1)",  text: "var(--accent)",   border: "rgba(255,177,98,0.25)",  dot: "var(--accent)"   },
  info:    { bg: "rgba(107,165,212,0.1)", text: "var(--info)",     border: "rgba(107,165,212,0.25)", dot: "var(--info)"     },
};

const sizeStyles = { sm: "h-5 px-2 text-[11px]", md: "h-6 px-2.5 text-xs" };

export function StatusPill({
  label,
  variant = "neutral",
  icon,
  dot = false,
  size = "sm",
  className,
}: StatusPillProps) {
  const v = variantStyles[variant];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border font-medium whitespace-nowrap",
        sizeStyles[size],
        className
      )}
      style={{ background: v.bg, color: v.text, borderColor: v.border }}
    >
      {dot && (
        <span
          className="h-1.5 w-1.5 rounded-full shrink-0"
          style={{ background: v.dot }}
        />
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
    </span>
  );
}
