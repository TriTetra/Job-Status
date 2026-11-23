/** Job feeds CareerOS reads (careeros/jobs/sources/feeds). Their terms ask to be credited. */
export const FEED_LABELS: Record<string, string> = {
  hackernews: "Hacker News",
  arbeitnow: "Arbeitnow",
  remotive: "Remotive",
  himalayas: "Himalayas",
  adzuna: "Adzuna",
  jobicy: "Jobicy",
};

export const feedLabel = (source: unknown): string | null =>
  typeof source === "string" ? FEED_LABELS[source] ?? null : null;
