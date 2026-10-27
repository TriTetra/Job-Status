/**
 * Decision Contract v1 — Frontend Types
 * Matches backend decision_builder.py schema exactly.
 */

export type Tier = "strong" | "look" | "low";
export type CriterionState = "confirmed" | "conflict" | "unknown";
export type NextActionType = "apply" | "investigate" | "skip";
export type UserDecisionStatus =
  | "unreviewed"
  | "shortlisted"
  | "applied"
  | "interviewing"
  | "offer"
  | "skipped";

export interface Semantic {
  tier: Tier;
  label: string; // "Strong match" | "Worth a look" | "Low fit"
  secondary?: string | null; // "High career value" | null
}

export interface Criterion {
  key: string; // "work_style" | "location" | "compensation" | "visa"
  label: string;
  state: CriterionState;
  detail: string;
}

export interface NextAction {
  type: NextActionType;
  label: string;
  reason: string;
}

export interface Decision {
  v: number;
  semantic: Semantic;
  criteria: Criterion[];
  next_action: NextAction;
  reasoning: string | null;
  reasoning_source: "llm" | "template" | null;
  generated_at: string | null;
}

export interface UserDecision {
  status: UserDecisionStatus;
  decided_at: string | null;
}

export interface Opportunity {
  url: string;
  career_score: number | null;
  fit_score: number | null;
  acceptance_probability: number | null;
  career_value: number | null;
  market_demand: number | null;
  expected_value: number | null;
  recommendation: "APPLY" | "CONSIDER" | "SKIP";
  skill_gaps: string[];
  explanation: Record<string, any>;
  scanned_at: string | null;
  decision?: Decision;
  user_decision: UserDecision;
}

export interface OpportunityListResponse {
  total: number;
  jobs: Opportunity[];
}

// Scan overlay states
export type ScanState = "idle" | "running" | "done" | "failed";
export type ScanPhase = "starting" | "profile" | "fetch" | "score";

export interface ScanJob {
  job_id: string;
  status: ScanState;
  phase: ScanPhase;
  progress: number;
  logs: Array<{ timestamp: string; message: string }>;
  result?: {
    total_jobs: number;
    scored: number;
    saved_to_db: number;
    apply: number;
    consider: number;
    skip: number;
  };
  error?: string;
}
