import { unstable_rethrow } from "next/navigation";
import { getSavedIdentity } from "@/features/onboarding/server";
import { SettingsShell, type InitialProfile, type ProfileData } from "./_components/settings-shell";

export default async function SettingsPage() {
  let initialProfile: InitialProfile | null = null;
  try {
    const id = await getSavedIdentity();
    initialProfile = {
      profileData: (id.profile_data ?? {}) as ProfileData,
      yearsInRole: Number(id.years_in_role ?? 0),
      careerLevel: id.career_level ?? "mid",
      currentRoleId: id.current_role_id ?? (id.current_custom_role_id ? `custom_${id.current_custom_role_id}` : ""),
      email: id.email ?? "",
    };
  } catch (err) {
    unstable_rethrow(err); // Next.js control-flow errors are not ours to swallow
    // The tabs still load their own data; the profile tab starts blank
    console.error("[settings] profile load failed:", err);
  }

  return <SettingsShell initialProfile={initialProfile} />;
}
