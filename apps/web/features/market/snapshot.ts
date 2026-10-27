import type { MarketSignal, MarketSnapshot, MarketSummary, SkillTrend, TimeRange } from "./types";

type Get = <T>(path: string) => Promise<T>;

export const DEFAULT_RANGE: TimeRange = "7d";
const TRENDED_SKILLS = 5;

export function toDays(range: TimeRange): number {
  return range === "7d" ? 7 : range === "30d" ? 30 : 90;
}

/**
 * Summary + recent signals + trends for the top skills.
 * Shared by the server page (first render) and the client view (range changes);
 * `get` is serverApiFetch or apiFetch. A failing trend is skipped, not fatal.
 */
export async function loadMarketSnapshot(get: Get, range: TimeRange): Promise<MarketSnapshot> {
  const days = toDays(range);
  const [summary, signals] = await Promise.all([
    get<MarketSummary>(`/api/market/summary?days=${days}`),
    get<MarketSignal[]>(`/api/market/signals?days=${days}&limit=20`),
  ]);
  const trends = await Promise.all(
    (summary.top_skills ?? []).slice(0, TRENDED_SKILLS).map((s) =>
      get<SkillTrend>(`/api/market/trend/${encodeURIComponent(s.skill)}?days=${days}`).catch(() => null),
    ),
  );
  return { summary, signals, trends: trends.filter((t): t is SkillTrend => t !== null) };
}
