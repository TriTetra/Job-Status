/** Market: the user's own matching postings (GET /api/market/jobs) + news signals (HN, TechCrunch). */

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

export interface SkillDemand {
  name: string;
  open_jobs: number;
  share: number;
  /** change in share, percentage points, this period vs the one before (null: too few postings) */
  trend_pts: number | null;
  you_show: boolean;
  missing_in_your_matches: number;
}

export interface OwnMarket {
  days: number;
  open_matches: number;
  new_this_period: number;
  new_last_period: number;
  change_pct: number | null;
  salary: { currency: string; median: number; low: number; high: number; postings: number } | null;
  salary_stated_share: number | null;
  remote_share: number | null;
  visa: { sponsor_share: number; stated: number } | null;
  skills: SkillDemand[];
  busiest_companies: Array<{ key: string | null; name: string; new: number }>;
}

export type Period = 30 | 90;

export interface MarketData {
  own: OwnMarket;
  news: MarketSignal[];
}
