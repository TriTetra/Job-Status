"use client";

import { cn } from "@/lib/utils";
import { LabelText } from "@/components/shared/label-text";
import { MetricText } from "@/components/shared/metric-text";
import { NarrativeText } from "@/components/shared/narrative-text";

export type StageVariant = "neutral" | "accent" | "warning" | "success" | "danger";

export interface ApplicationCard {
  company: string;
  role: string;
  score?: number;
  daysAgo?: string;
  nextAction?: string;
  variant?: StageVariant;
  onClick?: () => void;
}

interface PipelineStageProps {
  name: string;
  count: number;
  variant?: StageVariant;
  cards: ApplicationCard[];
  onAdd?: () => void;
  className?: string;
}

const variantDot: Record<StageVariant, string> = {
  neutral: "var(--text-muted)",
  accent:  "var(--accent)",
  warning: "var(--warning)",
  success: "var(--success)",
  danger:  "var(--danger)",
};

const variantCount: Record<StageVariant, { bg: string; color: string }> = {
  neutral: { bg: "var(--surface-hover)",            color: "var(--text-secondary)" },
  accent:  { bg: "rgba(255,177,98,0.15)",            color: "var(--accent)" },
  warning: { bg: "rgba(255,177,98,0.15)",            color: "var(--warning)" },
  success: { bg: "rgba(127,182,133,0.15)",           color: "var(--success)" },
  danger:  { bg: "rgba(201,106,90,0.15)",            color: "var(--danger)" },
};

function CompactApplicationCard({ card }: { card: ApplicationCard }) {
  return (
    <button
      onClick={card.onClick}
      className="w-full text-left surface p-3 hover:bg-surface-hover transition-colors rounded-lg"
    >
      <div className="flex items-center justify-between mb-1">
        <NarrativeText size="sm" weight="medium" className="truncate">
          {card.company}
        </NarrativeText>
        {card.score !== undefined && (
          <MetricText value={card.score} size="sm" showTrendIcon={false} />
        )}
      </div>
      <div className="text-xs truncate mb-1.5" style={{ color: "var(--text-muted)" }}>
        {card.role}
      </div>
      <div className="flex items-center justify-between text-[11px]">
        {card.daysAgo && (
          <span style={{ color: "var(--text-muted)" }}>{card.daysAgo}</span>
        )}
        {card.nextAction && (
          <span className="font-medium" style={{ color: "var(--accent)" }}>{card.nextAction}</span>
        )}
      </div>
    </button>
  );
}

export function PipelineStage({
  name,
  count,
  variant = "neutral",
  cards,
  onAdd,
  className,
}: PipelineStageProps) {
  const dot = variantDot[variant];
  const countStyle = variantCount[variant];

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: dot }} />
          <LabelText>{name}</LabelText>
        </div>
        <span
          className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded text-[11px] font-medium tabular-nums"
          style={{ background: countStyle.bg, color: countStyle.color }}
        >
          {count}
        </span>
      </div>

      <div className="space-y-2 flex-1">
        {cards.map((card, i) => (
          <CompactApplicationCard key={i} card={card} />
        ))}
        {cards.length === 0 && (
          <div className="text-center py-6 text-xs" style={{ color: "var(--text-muted)" }}>
            No applications
          </div>
        )}
      </div>

      {onAdd && (
        <button
          onClick={onAdd}
          className="mt-2 w-full h-8 rounded-lg border border-dashed text-xs transition-colors"
          style={{
            borderColor: "var(--border)",
            color: "var(--text-muted)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "var(--text-primary)";
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-strong)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
          }}
        >
          + Add
        </button>
      )}
    </div>
  );
}
