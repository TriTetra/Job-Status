import type { SavedIdentity } from "@/features/onboarding/server";

/** users.profile_data as written by the identity step. */
export interface ProfileData {
  first_name?: string;
  last_name?: string | null;
  country?: string;
  current_role_title?: string;
  total_years?: number | null;
  languages?: Array<{ code: string; level: string }>;
  education_level?: string | null;
  [key: string]: unknown;
}

export interface InitialProfile {
  profileData: ProfileData;
  yearsInRole: number;
  careerLevel: string;
  currentRoleId: string;
  email: string;
}

export function toInitialProfile(id: SavedIdentity): InitialProfile {
  return {
    profileData: (id.profile_data ?? {}) as ProfileData,
    yearsInRole: Number(id.years_in_role ?? 0),
    careerLevel: id.career_level ?? "mid",
    currentRoleId: id.current_role_id ?? (id.current_custom_role_id ? `custom_${id.current_custom_role_id}` : ""),
    email: id.email ?? "",
  };
}
