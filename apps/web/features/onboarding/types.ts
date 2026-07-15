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
  goals: Record<string, unknown>;
  next_step: OnboardingState | null;
}
