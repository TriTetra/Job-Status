import { sql } from "./client";

export const STATE_TO_URL: Record<string, string> = {
  NOT_STARTED: "/onboarding?step=IDENTITY",
  IDENTITY:    "/onboarding?step=IDENTITY",
  GOALS:       "/onboarding?step=GOALS",
  EVIDENCE:    "/onboarding?step=EVIDENCE",
  CONNECTIONS: "/onboarding?step=CONNECTIONS",
  BUILDING:    "/onboarding?step=BUILDING",
};

export async function getOnboardingState(clerkId: string): Promise<string> {
  const rows = await sql`
    SELECT onboarding_state FROM users WHERE clerk_id = ${clerkId}
  `;
  console.log("[onboarding] state query result:", rows[0] ?? "no row");
  return (rows[0]?.onboarding_state as string | undefined) ?? "NOT_STARTED";
}
