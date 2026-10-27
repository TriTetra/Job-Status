export interface MarketSignal {
  id: number;
  signal_type: string;
  source: string;
  title: string;
  impact: string;
  occurred_at: string;
  companies_affected: string[];
  skills_affected: string[];
  summary?: string;
  url?: string | null;
}

export interface MarketSummary {
  period_days: number;
  signal_counts: Record<string, number>;
  top_companies: { name: string; count: number }[];
  top_skills: { skill: string; count: number }[];
}

export interface SkillTrend {
  skill: string;
  current_count: number;
  previous_count: number;
  change_percent: number;
  direction: "up" | "down" | "stable";
}

export type TimeRange = "7d" | "30d" | "90d";

export interface MarketSnapshot {
  summary: MarketSummary;
  signals: MarketSignal[];
  trends: SkillTrend[];
}
