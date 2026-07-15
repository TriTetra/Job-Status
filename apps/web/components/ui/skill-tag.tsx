import { cn } from "@/lib/utils";
import { X, AlertCircle, Check } from "lucide-react";

export type SkillTagVariant = "default" | "matched" | "gap" | "emphasized";

interface SkillTagProps {
  name: string;
  confidence?: number;
  variant?: SkillTagVariant;
  removable?: boolean;
  onRemove?: () => void;
  onClick?: () => void;
  className?: string;
}

const variantStyles: Record<SkillTagVariant, { bg: string; text: string; border: string }> = {
  default:    { bg: "var(--surface)",              text: "var(--text-secondary)", border: "var(--border)"              },
  matched:    { bg: "rgba(127,182,133,0.1)",       text: "var(--success)",        border: "rgba(127,182,133,0.25)"    },
  gap:        { bg: "rgba(201,106,90,0.1)",        text: "var(--danger)",         border: "rgba(201,106,90,0.25)"     },
  emphasized: { bg: "rgba(255,177,98,0.1)",        text: "var(--accent)",         border: "rgba(255,177,98,0.3)"      },
};

export function SkillTag({
  name,
  confidence,
  variant = "default",
  removable = false,
  onRemove,
  onClick,
  className,
}: SkillTagProps) {
  const v = variantStyles[variant];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md border text-xs font-medium transition-colors",
        onClick && "cursor-pointer",
        className
      )}
      style={{ background: v.bg, color: v.text, borderColor: v.border }}
      onClick={onClick}
    >
      {variant === "matched" && <Check className="h-3 w-3" strokeWidth={2.5} />}
      {variant === "gap" && <AlertCircle className="h-3 w-3" strokeWidth={2} />}
      <span>{name}</span>
      {confidence !== undefined && (
        <span className="font-mono text-[10px] opacity-60 tabular-nums">{confidence}%</span>
      )}
      {removable && onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="ml-0.5 h-4 w-4 rounded-sm flex items-center justify-center transition-colors hover:bg-black/20"
          aria-label={`Remove ${name}`}
        >
          <X className="h-3 w-3" strokeWidth={2.5} />
        </button>
      )}
    </span>
  );
}
