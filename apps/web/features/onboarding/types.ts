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
