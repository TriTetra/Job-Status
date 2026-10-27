import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import postgres from "postgres";
import { SettingsShell, type InitialProfile } from "./_components/settings-shell";

const sql = postgres(process.env.DATABASE_URL!);

export default async function SettingsPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  let initialProfile: InitialProfile | null = null;
  try {
    const rows = await sql`
      SELECT profile_data, years_in_role, career_level,
             current_role_id, current_custom_role_id, email
      FROM users
      WHERE clerk_id = ${userId}
      LIMIT 1
    `;
    if (rows[0]) {
      const r = rows[0];
      initialProfile = {
        profileData: (r.profile_data as Record<string, any>) ?? {},
        yearsInRole: Number(r.years_in_role ?? 0),
        careerLevel: (r.career_level as string) ?? "mid",
        currentRoleId:
          (r.current_role_id as string) ??
          (r.current_custom_role_id ? `custom_${r.current_custom_role_id}` : ""),
        email: (r.email as string) ?? "",
      };
    }
  } catch (err) {
    console.error("[settings] profile load failed:", err);
  }

  return <SettingsShell initialProfile={initialProfile} />;
}
