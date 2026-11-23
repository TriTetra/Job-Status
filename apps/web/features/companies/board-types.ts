/** GET /api/companies/boards — companies as the job boards show them (careeros/companies/directory.py). */

export type HiringTrend = "spike" | "up" | "stable" | "down";

export interface AskedSkill {
  name: string;
  jobs: number;
  you_show: boolean;
}

export interface BoardCompany {
  key: string;
  name: string;
  ats: string;
  /** the company website (board, else its postings): the company card matches public records on it */
  domain?: string | null;
  open_roles: number;
  new_this_week: number;
  new_last_week: number;
  closed_this_week: number;
  trend: HiringTrend;
  your_matches: number;
  your_strong: number;
  best_score: number | null;
  remote_share: number | null;
  top_skills: AskedSkill[];
  skills_you_show: number;
  last_synced_at: string | null;
  sync_error: boolean;
  profile: {
    tier: string;
    industry: string | null;
    headquarters: string | null;
    sponsors_visa: boolean | null;
    employee_count: number | null;
    salary_ranges?: Record<string, unknown>;
    interview_rounds?: unknown[];
    culture_signals?: unknown[];
  } | null;
}

export interface CompanyRole {
  url: string;
  title: string;
  location: string;
  remote: boolean;
  posted_at: string | null;
  score: number | null;
  recommendation: string | null;
  application_url: string;
  skills: string[];
}

export interface BoardCompanyDetail extends BoardCompany {
  roles: CompanyRole[];
  /** Postings first seen per week, oldest first; the last bar is this week */
  weekly_new: number[];
}
