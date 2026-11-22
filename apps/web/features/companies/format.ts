import type { BoardCompany, HiringTrend } from "./board-types";

export const TREND: Record<HiringTrend, { label: string; color: string }> = {
  spike: { label: "hiring fast", color: "var(--success)" },
  up: { label: "picking up", color: "var(--success)" },
  stable: { label: "steady", color: "var(--text-muted)" },
  down: { label: "slowing", color: "var(--warning)" },
};

export function weekLine(c: BoardCompany): string {
  if (!c.new_this_week && !c.closed_this_week) return "no change this week";
  const parts = [];
  if (c.new_this_week) parts.push(`+${c.new_this_week} new`);
  if (c.closed_this_week) parts.push(`${c.closed_this_week} closed`);
  return `${parts.join(", ")} this week`;
}

export function fitLine(c: BoardCompany): string | null {
  if (!c.your_matches) return null;
  const strong = c.your_strong ? ` · ${c.your_strong} strong` : "";
  const best = c.best_score != null ? ` · best ${c.best_score}` : "";
  return `${c.your_matches} ${c.your_matches === 1 ? "fits" : "fit"} you${strong}${best}`;
}

export function profileLine(c: BoardCompany): string {
  const p = c.profile;
  const tier = p?.tier === "big_tech" ? "Big Tech" : p?.tier === "unicorn" ? "Unicorn" : null;
  return [p?.industry, p?.headquarters, tier].filter(Boolean).join(" · ");
}
