/**
 * Digest facts (GET /api/briefing) → the briefing the page renders. Pure: no I/O.
 */

import { displayName, safeHttpUrl } from "@/lib/utils";
import type { DigestFacts, HeadlineFact } from "./facts";
import type { BriefingHeadline, BriefingView, ChangeLine, WeekNumber } from "./types";
import { closingFor, leadFor, timeGreeting } from "./templates";

/**
 * "Now" as a wall clock in the user's time zone: a Date whose getHours()/getDay()
 * read the user's local hour and weekday. Unknown or missing zone → server clock.
 */
export function zonedNow(tz: string | undefined, now: Date = new Date()): Date {
  if (!tz) return now;
  try {
    return new Date(now.toLocaleString("en-US", { timeZone: decodeURIComponent(tz) }));
  } catch {
    return now;
  }
}

/** Opportunities deep link: the inbox with this job selected. */
export const inboxHref = (url: string) => `/inbox?job=${encodeURIComponent(url)}`;

const DAY_MS = 86_400_000;

function ago(iso: string | null, now: Date): string | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return null;
  const days = Math.floor((now.getTime() - t) / DAY_MS);
  if (days <= 0) return "posted today";
  if (days === 1) return "posted yesterday";
  if (days < 30) return `posted ${days} days ago`;
  return `posted ${Math.floor(days / 30)} mo ago`;
}

function money(salary: HeadlineFact["salary"]): string | null {
  if (!salary || !(salary.min || salary.max)) return null;
  const fmt = new Intl.NumberFormat("en", {
    style: "currency",
    currency: salary.currency || "USD",
    notation: "compact",
    maximumFractionDigits: 0,
  });
  if (salary.min && salary.max) return `${fmt.format(salary.min)}–${fmt.format(salary.max)}`;
  return salary.min ? `${fmt.format(salary.min)}+` : `up to ${fmt.format(salary.max as number)}`;
}

function whyFor(h: HeadlineFact): string {
  if (h.reasoning) return h.reasoning;
  const strong = h.matched.slice(0, 3);
  const parts: string[] = [];
  if (strong.length) parts.push(`Your evidence covers ${strong.join(", ")}`);
  if (h.gaps.length) parts.push(`the gap is ${h.gaps.slice(0, 2).join(" and ")}`);
  const sentence = parts.join("; ");
  return sentence ? `${sentence}.` : h.next_action ?? "Your strongest open match right now.";
}

function headlineView(h: HeadlineFact, now: Date): BriefingHeadline {
  const where = h.remote ? "Remote" : h.location;
  const meta = [where, money(h.salary), ago(h.posted_at, now)].filter(Boolean).join(" · ");
  return {
    url: h.url,
    company: h.company,
    companyKey: h.company_key ?? null,
    title: h.title,
    score: h.score,
    recommendation: h.recommendation,
    chance: h.chance,
    why: whyFor(h),
    meta,
    criteria: h.criteria.filter((c) => c.label).map((c) => ({ label: c.label, state: c.state })),
    postingUrl: safeHttpUrl(h.application_url) ?? safeHttpUrl(h.url),
    inboxHref: inboxHref(h.url),
  };
}

function changeLines(f: DigestFacts): ChangeLine[] {
  const c = f.changes;
  const lines: ChangeLine[] = [];
  if (c.new_matches > 0) {
    lines.push({
      text:
        `${c.new_matches} new ${c.new_matches === 1 ? "match" : "matches"} fit your roles` +
        (c.new_strong ? `; ${c.new_strong} ${c.new_strong === 1 ? "is" : "are"} strong.` : "."),
      href: "/inbox",
      linkLabel: "See them",
    });
  }
  for (const co of c.busy_companies) {
    lines.push({ text: `${co.name} posted ${co.count} roles that fit you.`, href: "/inbox", linkLabel: "Open" });
  }
  for (const job of c.closed_tracked) {
    lines.push({ text: `${job.title} at ${job.company} has closed.` });
  }
  if (lines.length === 0 && f.has_scores) {
    lines.push({ text: "Nothing new since your last visit. The company boards are re-read every 6 hours." });
  }
  return lines;
}

function weekNumbers(f: DigestFacts): WeekNumber[] {
  const w = f.week;
  const delta = w.strong_this_week - w.strong_last_week;
  return [
    {
      value: String(w.strong_this_week),
      label: "strong matches this week",
      note: w.strong_last_week || delta ? `${delta >= 0 ? "+" : ""}${delta} vs last week` : undefined,
    },
    { value: String(w.applied_this_week), label: "applications sent this week" },
    { value: String(w.open_strong), label: "strong matches open now", note: `of ${w.open_matches} matches` },
  ];
}

function dateline(f: DigestFacts, now: Date): string {
  const day = now.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
  const h = f.hours_since_last_visit;
  if (h == null) return day;
  const since = h < 24 ? `${Math.round(h)} hours` : `${Math.round(h / 24)} ${Math.round(h / 24) === 1 ? "day" : "days"}`;
  return `${day} · ${since} since your last visit`;
}

export function buildBriefing(f: DigestFacts, now: Date = new Date()): BriefingView {
  const name = displayName(f.first_name);
  const changes = changeLines(f);
  return {
    dateline: dateline(f, now),
    greeting: `${timeGreeting(now.getHours())}${name ? `, ${name}` : ""}.`,
    lead: leadFor(f.tone, {
      newMatches: f.changes.new_matches,
      newStrong: f.changes.new_strong,
      todos: f.todos.length,
      hasScores: f.has_scores,
    }),
    headline: f.headline ? headlineView(f.headline, now) : null,
    changes,
    todos: f.todos,
    week: f.has_scores ? weekNumbers(f) : [],
    closing: closingFor(f.tone, now.getHours(), now.getDay()),
  };
}
