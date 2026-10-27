import type { BriefingResult } from "./types";
import { auth } from "@clerk/nextjs/server";
import { getBriefingData } from "@/lib/db/dashboard";

/**
 * Fetches today's briefing from Postgres (server-side, direct DB).
 * - No signed-in user  -> quiet empty state
 * - DB error           -> propagates to briefing/error.tsx (retry UI)
 */
export async function getBriefing(): Promise<BriefingResult> {
  const { userId } = await auth();

  if (!userId) {
    return {
      status: "empty",
      data: { watching: ["Sign in to see your personalized briefing."] },
    };
  }

  return getBriefingData(userId);
}
