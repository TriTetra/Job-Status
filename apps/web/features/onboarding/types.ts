export type OnboardingState =
  | "NOT_STARTED"
  | "IDENTITY"
  | "GOALS"
  | "EVIDENCE"
  | "CONNECTIONS"
  | "BUILDING"
  | "READY";

export const ONBOARDING_STEPS: OnboardingState[] = [
  "IDENTITY",
  "GOALS",
  "EVIDENCE",
  "CONNECTIONS",
  "BUILDING",
];

export interface IdentityData {
  firstName: string;
  lastName: string;
  currentTitle: string;
  yearsOfExperience: number;
}

export interface GoalsData {
  targetRoles: string[];
  targetIndustries: string[];
  desiredSalaryMin?: number;
  desiredSalaryMax?: number;
  openToRemote: boolean;
}

export interface OnboardingData {
  identity?: IdentityData;
  goals?: GoalsData;
}

/** Shape returned by GET /api/onboarding/state */
export interface OnboardingStatus {
  state: OnboardingState;
  profile_data: Record<string, unknown>;
  preferences?: {
    goal_ids?: string[];
    preferred_role_ids?: string[];
    preferred_country_codes?: string[];
    work_arrangements?: string[];
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
