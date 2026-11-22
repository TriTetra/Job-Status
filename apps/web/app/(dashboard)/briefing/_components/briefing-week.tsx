import { SectionLabel } from "@/components/shared/narrative-section";
import type { WeekNumber } from "@/features/briefing/types";
import { Movement } from "./movement";

export function BriefingWeek({ numbers }: { numbers: WeekNumber[] }) {
  if (numbers.length === 0) return null;
  return (
    <Movement delay={360}>
      <SectionLabel>This week</SectionLabel>
      <dl className="grid grid-cols-1 sm:grid-cols-3 gap-8">
        {numbers.map((n) => (
          <div key={n.label}>
            <dd className="font-serif-display text-5xl tabular-nums" style={{ color: "var(--text-primary)" }}>{n.value}</dd>
            <dt className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>{n.label}</dt>
            {n.note && <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>{n.note}</p>}
          </div>
        ))}
      </dl>
    </Movement>
  );
}
