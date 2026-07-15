import type { BriefingResult } from "./types";
import { MOCK_BRIEFING } from "./mock";

/**
 * Fetches today's briefing. Backed by mock data for now —
 * swap the body for a real API call once the backend endpoint exists,
 * the BriefingResult shape is what the route already renders against.
 */
export async function getBriefing(): Promise<BriefingResult> {
  return MOCK_BRIEFING;
}
