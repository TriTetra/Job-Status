import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import { buildBriefing } from "./build";
import type { BriefingFacts } from "./facts";
import type { BriefingResult } from "./types";

/**
 * Today's briefing for the signed-in user (Server Components only).
 * API errors propagate to briefing/error.tsx (retry UI).
 */
export async function getBriefing(): Promise<BriefingResult> {
  return buildBriefing(await serverApiFetch<BriefingFacts>("/api/briefing"));
}
