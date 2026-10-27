import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import type { OnboardingState } from "./types";

/** The signed-in user's onboarding state (Server Components only). */
export async function getOnboardingState(): Promise<OnboardingState> {
  const res = await serverApiFetch<{ state: OnboardingState }>("/api/onboarding/state");
  return res.state;
}

/** What the identity step saved (GET /api/onboarding/identity). */
export interface SavedIdentity {
  profile_data: Record<string, unknown>;
  years_in_role: number | null;
  career_level: string | null;
  current_role_id: string | null;
  current_custom_role_id: string | null;
  email: string;
}

export async function getSavedIdentity(): Promise<SavedIdentity> {
  return serverApiFetch<SavedIdentity>("/api/onboarding/identity");
}
