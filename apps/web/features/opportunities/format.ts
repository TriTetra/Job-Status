/** How an opportunity reads on screen: chance, where, pay, age, status. Pure. */

import type { InboxPreferences, Opportunity, Tier } from "./types";
import { tierOf } from "./tier";

export type Chance = "high" | "medium" | "low";

/** Acceptance is stored 0–100; the score asks "is it good", chance asks "can I get it". */
export function chanceOf(o: Opportunity): Chance {
  const a = o.acceptance_probability ?? 0;
  return a >= 30 ? "high" : a >= 15 ? "medium" : "low";
}

export const CHANCE_LABEL: Record<Chance, string> = { high: "good chance", medium: "fair chance", low: "long shot" };
export const CHANCE_COLOR: Record<Chance, string> = {
  high: "var(--success)",
  medium: "var(--text-secondary)",
  low: "var(--text-muted)",
};
export const TIER_LABEL: Record<Tier, string> = { strong: "Strong", look: "Worth a look", low: "Low fit" };
export const TIER_COLOR: Record<Tier, string> = {
  strong: "var(--success)",
  look: "var(--accent)",
  low: "var(--text-muted)",
};

export function companyOf(o: Opportunity): string {
  if (o.explanation?.company) return o.explanation.company;
  try {
    return new URL(o.url).hostname.replace(/^www\./, "");
  } catch {
    return "Company";
  }
}

export function whereOf(o: Opportunity): string {
  const ex = o.explanation ?? {};
  if (ex.remote) return ex.remote_region ? `Remote · ${ex.remote_region}` : "Remote";
  const loc = (ex.location ?? "").split(";")[0].trim();
  return loc.length > 48 ? `${loc.slice(0, 46)}…` : loc;
}

export function salaryOf(o: Opportunity): string | null {
  const ex = o.explanation ?? {};
  const min = typeof ex.salary_min === "number" ? ex.salary_min : null;
  const max = typeof ex.salary_max === "number" ? ex.salary_max : null;
  if (!min && !max) return null;
  const currency = typeof ex.salary_currency === "string" && ex.salary_currency ? ex.salary_currency : "USD";
  let fmt: Intl.NumberFormat;
  try {
    fmt = new Intl.NumberFormat("en", { style: "currency", currency, notation: "compact", maximumFractionDigits: 0 });
  } catch {
    fmt = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 0 });
  }
  if (min && max) return `${fmt.format(min)}–${fmt.format(max)}`;
  return min ? `${fmt.format(min)}+` : `up to ${fmt.format(max as number)}`;
}

export function postedAgo(o: Opportunity, now = Date.now()): string | null {
  const iso = o.explanation?.posted_at;
  if (!iso) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return null;
  const days = Math.floor((now - t) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "1 day ago";
  if (days < 30) return `${days} days ago`;
  return `${Math.floor(days / 30)} mo ago`;
}

export function hasConflict(o: Opportunity): boolean {
  return (o.decision?.criteria ?? []).some((c) => c.state === "conflict");
}

export const DECISION_LABEL: Partial<Record<Opportunity["user_decision"]["status"], string>> = {
  shortlisted: "Shortlisted",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  skipped: "Skipped",
};

export type View = "strong" | "look" | "all" | "shortlisted" | "skipped";

/** Jobs for a view tab: skipped ones only under "Skipped"; acted-on ones under "Shortlisted". */
export function inView(o: Opportunity, view: View): boolean {
  const status = o.user_decision?.status ?? "unreviewed";
  if (view === "skipped") return status === "skipped";
  if (status === "skipped") return false;
  if (view === "shortlisted") return status !== "unreviewed";
  if (view === "all") return true;
  return tierOf(o) === view;
}

const TIER_ORDER: Record<Tier, number> = { strong: 0, look: 1, low: 2 };

export function byRank(a: Opportunity, b: Opportunity): number {
  return TIER_ORDER[tierOf(a)] - TIER_ORDER[tierOf(b)] || (b.career_score ?? 0) - (a.career_score ?? 0);
}

const ARRANGEMENT: Record<string, string> = { remote: "remote", hybrid: "hybrid", onsite: "on-site" };

function listing(items: string[]): string {
  if (items.length <= 1) return items[0] ?? "";
  return `${items.slice(0, -1).join(", ")} or ${items[items.length - 1]}`;
}

/** The saved search as one sentence: "Looking for AI Engineer roles, remote or hybrid, in DE, NL — from $85K / yr." */
export function rulesSentence(p: InboxPreferences | null): string | null {
  if (!p) return null;
  const roles = p.preferred_role_titles ?? [];
  const parts: string[] = [];
  parts.push(roles.length ? `${listing(roles.slice(0, 3))}${roles.length > 3 ? ` +${roles.length - 3}` : ""} roles` : "roles that fit your profile");
  const arr = (p.work_arrangements ?? []).map((a) => ARRANGEMENT[a] ?? a);
  if (arr.length) parts.push(listing(arr));
  const countries = p.preferred_country_codes ?? [];
  if (countries.length) parts.push(`in ${listing(countries.slice(0, 4))}${countries.length > 4 ? ` +${countries.length - 4}` : ""}`);
  let sentence = `Looking for ${parts.join(", ")}`;
  const min = p.salary?.min ?? p.salary_min;
  if (min) {
    let money: string;
    try {
      money = new Intl.NumberFormat("en", {
        style: "currency",
        currency: p.salary?.currency || "USD",
        notation: "compact",
        maximumFractionDigits: 1,
      }).format(min);
    } catch {
      money = String(min);
    }
    sentence += ` — from ${money} / ${p.salary?.period === "month" ? "mo" : "yr"}`;
  }
  if (p.requires_sponsorship === true) sentence += ", with visa sponsorship";
  return `${sentence}.`;
}
