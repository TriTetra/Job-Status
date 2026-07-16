import { neon } from "@neondatabase/serverless";

// Connects via HTTPS/WebSocket on port 443 — works without WARP
const sql = neon(process.env.DATABASE_URL!);

const STATE_TO_URL: Record<string, string> = {
  NOT_STARTED: "/onboarding?step=IDENTITY",
  IDENTITY:    "/onboarding?step=IDENTITY",
  GOALS:       "/onboarding?step=GOALS",
  EVIDENCE:    "/onboarding?step=EVIDENCE",
  CONNECTIONS: "/onboarding?step=CONNECTIONS",
  BUILDING:    "/onboarding?step=BUILDING",
};

export { STATE_TO_URL };

export async function getOnboardingState(clerkId: string): Promise<string> {
  const rows = await sql`
    SELECT onboarding_state FROM users WHERE clerk_id = ${clerkId}
  `;
  return (rows[0]?.onboarding_state as string | undefined) ?? "NOT_STARTED";
}
