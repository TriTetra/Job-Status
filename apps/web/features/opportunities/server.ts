import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import { ALL_OPPORTUNITIES, type Freshness } from "./api";
import type { InboxData, InboxPreferences, OpportunityListResponse } from "./types";

/** Opportunities + the preferences summarized in the header (preferences are optional). */
export async function getInbox(): Promise<InboxData> {
  const [list, prefs, freshness] = await Promise.all([
    serverApiFetch<OpportunityListResponse>(ALL_OPPORTUNITIES),
    serverApiFetch<InboxPreferences>("/api/preferences").catch(() => null),
    serverApiFetch<Freshness>("/api/jobs/freshness").catch(() => null),
  ]);
  return { jobs: list.jobs, prefs, freshness };
}
