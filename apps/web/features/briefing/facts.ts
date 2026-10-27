/**
 * Shape of GET /api/briefing (careeros/briefing/facts.py).
 * Facts only — the copy is composed in build.ts + templates.ts.
 */

import type { Recommendation } from "./types";
import type { Tone } from "./templates";

export interface CareerGraphStats {
  skills_count?: number;
  projects_count?: number;
  achievements_count?: number;
  companies_count?: number;
}

export interface OpportunityFact {
  url: string;
  career_score: number | null;
  recommendation: Recommendation | string | null;
  skill_gaps: string[];
  explanation: {
    company?: string;
    role?: string;
    title?: string;
    location?: string;
    why?: string[];
    matched_skills?: unknown[];
  };
}

export interface HiringCompanyFact {
  name: string;
  hiring_trend: string;
  open_positions_count: number;
}

export interface BriefingFacts {
  first_name: string | null;
  career_graph_stats: CareerGraphStats;
  opportunities: OpportunityFact[];
  evidence: { total: number; skill_count: number; avg_confidence: number };
  hiring_companies: HiringCompanyFact[];
  last_24h: { new_evidence: number; new_scores: number };
  live_applications: { company: string | null; title: string; status: "interview" | "offer" }[];
  github_connected: boolean;
  tone: Tone;
}
