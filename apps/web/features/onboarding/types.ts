export type OnboardingState =
  | "NOT_STARTED"
  | "IDENTITY"
  | "GOALS"
  | "EVIDENCE"
  | "CONNECTIONS"
  | "BUILDING"
  | "READY";



/** Shape returned by GET /api/onboarding/state */
export interface OnboardingStatus {
  state: OnboardingState;
  profile_data: Record<string, unknown>;
  preferences?: {
    goal_ids?: string[];
    preferred_role_ids?: string[];
    preferred_country_codes?: string[];
    work_arrangements?: string[];
    requires_sponsorship?: boolean;
    contract_types?: string[];
    availability?: string | null;
    target_seniority?: string | null;
    salary?: {
      min?: number;
      max?: number;
      currency?: string;
      period?: string;
      negotiable?: boolean;
    };
  };
  next_step: OnboardingState | null;
}

// ── API wire types ────────────────────────────────────────────────────────────

/** Background job as polled from …/{job_id}/status (careeros/shared/background.py). */
export interface JobStatus<R = unknown> {
  job_id: string;
  status: string;
  progress: number;
  logs: Array<{ timestamp: string; message: string; type?: string }>;
  result: R | null;
  error: string | null;
  created_at: string;
}

export interface CareerGraphNode {
  id: string;
  type: string;
  label: string;
  confidence: number;
  metadata: Record<string, unknown>;
}

export interface CareerGraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface CareerGraphData {
  nodes: CareerGraphNode[];
  edges: CareerGraphEdge[];
  stats: Record<string, number>;
}

export interface ExtractionSummary {
  skills_extracted: number;
  experience_count: number;
  projects_count: number;
  evidence_items: number;
}

/** evidence_items.evidence_data — free-form JSON; these keys are the ones the UI reads. */
export interface EvidenceData {
  type?: string;
  technologies?: string[];
  description?: string;
  company?: string;
  role?: string;
  duration?: string;
  [key: string]: unknown;
}

export interface EvidenceReviewItem {
  id: string;
  name: string;
  skill_id: number | null;
  confidence: number;
  source: string;
  source_url: string | null;
  evidence_text: string | null;
  evidence_data: EvidenceData;
  created_at: string | null;
}

export interface EvidenceReview {
  skills: EvidenceReviewItem[];
  projects: EvidenceReviewItem[];
  experiences: EvidenceReviewItem[];
  education: EvidenceReviewItem[];
  certifications: EvidenceReviewItem[];
}

export interface GithubStatus {
  connected: boolean;
  username?: string;
  provider_user_id?: string;
  metadata?: { avatar_url?: string; public_repos?: number; followers?: number; bio?: string | null };
  last_synced_at?: string | null;
}

export interface PortfolioStatus {
  connected: boolean;
  url?: string;
  last_synced_at?: string | null;
}
