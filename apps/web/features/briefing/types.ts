/** The briefing as the page renders it (built from DigestFacts by build.ts). */

import type { Chance, CriterionState, TodoFact } from "./facts";

export interface BriefingHeadline {
  url: string;
  company: string;
  companyKey: string | null;
  title: string;
  score: number;
  recommendation: "APPLY" | "CONSIDER" | "SKIP";
  chance: Chance;
  /** One or two sentences on why this job — the cached "why", or composed from skills */
  why: string;
  /** "Remote · $90K+ / yr · posted 2 days ago" */
  meta: string;
  criteria: Array<{ label: string; state: CriterionState }>;
  postingUrl: string | null;
  inboxHref: string;
}

export interface ChangeLine {
  text: string;
  href?: string;
  linkLabel?: string;
}

export interface WeekNumber {
  value: string;
  label: string;
  note?: string;
}

export interface BriefingView {
  /** "Sunday, 22 November · 26 hours since your last visit" */
  dateline: string;
  greeting: string;
  /** One sentence that sums the visit up */
  lead: string;
  headline: BriefingHeadline | null;
  changes: ChangeLine[];
  todos: TodoFact[];
  week: WeekNumber[];
  closing: string[];
}
