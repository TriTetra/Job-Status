import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

interface LabelTextProps {
  children: ReactNode;
  uppercase?: boolean;
  muted?: boolean;
  accent?: boolean;
  style?: React.CSSProperties;
  className?: string;
}

export function LabelText({
  children,
  uppercase = true,
  muted = true,
  accent = false,
  style,
  className,
}: LabelTextProps) {
  return (
    <span
      className={cn(
        "text-[11px] font-medium tracking-wider",
        uppercase && "uppercase",
        accent
          ? "text-[var(--accent)]"
          : muted
          ? "text-[var(--text-muted)]"
          : "text-[var(--text-secondary)]",
        className
      )}
      style={style}
    >
      {children}
    </span>
  );
}
