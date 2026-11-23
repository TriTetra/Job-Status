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

/** GET /api/market/pay (careeros/market/pay.py): stated pay by country and role family, plus official figures. */
export interface PayStats {
  postings: number;
  median?: number;
  p25?: number;
  p75?: number;
}

export interface OfficialPay {
  country: string;
  occupation: string;
  median: number;
  currency: string;
  period: string;
  reference: string;
  population: string;
  source: string;
  url: string;
}

export interface PayCountry {
  code: string;
  currency: string | null;
  all: PayStats;
  families: Array<PayStats & { family: string; examples: string[] }>;
  official: OfficialPay[];
}

export interface PayByCountry {
  window_days: number;
  min_postings: number;
  as_of: string;
  countries: PayCountry[];
}

export interface MarketData {
  own: OwnMarket;
  news: MarketSignal[];
  pay: PayByCountry | null;
}
