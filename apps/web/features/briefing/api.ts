import "server-only";

import { cookies } from "next/headers";
import { serverApiFetch } from "@/lib/api/server";

import { buildBriefing, zonedNow } from "./build";
import type { DigestFacts } from "./facts";
import type { BriefingView } from "./types";

/**
 * Today's briefing for the signed-in user (Server Components only), in the user's
 * time zone. API errors propagate to briefing/error.tsx (retry UI).
 */
export async function getBriefing(): Promise<BriefingView> {
  const tz = (await cookies()).get("careeros_tz")?.value;
  return buildBriefing(await serverApiFetch<DigestFacts>("/api/briefing"), zonedNow(tz));
}
