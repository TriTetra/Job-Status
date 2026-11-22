/**
 * GET /api/briefing (v2) — what changed since the last visit and what to do.
 * Matches careeros/briefing/digest.py.
 */

export type Tone = "warm" | "direct" | "analytical";
export type Chance = "low" | "medium" | "high";
export type CriterionState = "confirmed" | "conflict" | "unknown";

export interface HeadlineFact {
  url: string;
  company: string;
  company_key: string | null;
  title: string;
  location: string;
  remote: boolean;
  score: number;
  recommendation: "APPLY" | "CONSIDER" | "SKIP";
  chance: Chance;
  reasoning: string | null;
  next_action: string | null;
  criteria: Array<{ label: string; state: CriterionState; detail: string }>;
  matched: string[];
  gaps: string[];
  posted_at: string | null;
  salary: { min: number | null; max: number | null; currency: string } | null;
  application_url: string;
  summary: string | null;
}

export interface TodoFact {
  key: string;
  kind: "offer" | "interview" | "scan" | "followup" | "shortlist" | "gap" | "sources";
  title: string;
  detail: string;
  cta_label: string;
  cta_href: string;
  external?: boolean;
}

export interface DigestFacts {
  v: 2;
  first_name: string | null;
  tone: Tone;
  since: string;
  hours_since_last_visit: number | null;
  headline: HeadlineFact | null;
  changes: {
    new_matches: number;
    new_strong: number;
    busy_companies: Array<{ name: string; count: number }>;
    closed_tracked: Array<{ company: string; title: string }>;
  };
  todos: TodoFact[];
  week: {
    strong_this_week: number;
    strong_last_week: number;
    applied_this_week: number;
    open_strong: number;
    open_matches: number;
  };
  evidence: { total: number; skill_count: number; avg_confidence: number };
  has_scores: boolean;
}
