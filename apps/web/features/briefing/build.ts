/**
 * Facts (GET /api/briefing) → the briefing the page renders. Pure: no I/O.
 */

import type { BriefingFacts, CareerGraphStats, HiringCompanyFact, OpportunityFact } from "./facts";
import type {
  BriefingData,
  BriefingResult,
  EvidenceSignal,
  EvidenceSummary,
  Opportunity,
  ProgressSummary,
  Recommendation,
} from "./types";
import {
  type BriefingContext,
  briefFor,
  closingFor,
  focusCandidates,
  greetingFor,
  subtitleFor,
  timeGreeting,
} from "./templates";

const FOCUS_NUMBERS = ["01", "02", "03"] as const;

export function buildBriefing(facts: BriefingFacts, now: Date = new Date()): BriefingResult {
  const stats = facts.career_graph_stats;
  const ev = facts.evidence;
  const skillCount = stats.skills_count ?? ev.skill_count ?? 0;

  if (ev.total === 0 && facts.opportunities.length === 0) {
    return {
      status: "empty",
      data: {
        greeting: timeGreeting(now.getHours()),
        watching: buildWatchingList(facts.hiring_companies),
        stats: {
          skills_count: skillCount,
          projects_count: stats.projects_count ?? 0,
          achievements_count: stats.achievements_count ?? 0,
          companies_count: stats.companies_count ?? 0,
        },
      },
    };
  }

  const opportunities = facts.opportunities.map(mapOpportunity);
  const topCompany = facts.hiring_companies[0];
  const ctx: BriefingContext = {
    hour: now.getHours(),
    dow: now.getDay(),
    skillCount,
    projectCount: stats.projects_count ?? 0,
    achievementCount: stats.achievements_count ?? 0,
    opportunityCount: opportunities.length,
    topOpportunity: opportunities[0] ? { company: opportunities[0].company, score: opportunities[0].score } : null,
    hiringCompany: topCompany ? { name: topCompany.name, openRoles: topCompany.open_positions_count } : null,
    newEvidence24h: facts.last_24h.new_evidence,
    newScores24h: facts.last_24h.new_scores,
    interviews: facts.live_applications
      .filter((a) => a.status === "interview")
      .map((a) => ({ company: a.company ?? "", title: a.title })),
    offers: facts.live_applications
      .filter((a) => a.status === "offer")
      .map((a) => ({ company: a.company ?? "", title: a.title })),
    githubConnected: facts.github_connected,
    tone: facts.tone,
  };

  const data: BriefingData = {
    greeting: { name: facts.first_name ?? "there", greeting: greetingFor(ctx), subtitle: subtitleFor(ctx) },
    brief: briefFor(ctx),
    focus: focusCandidates(ctx).slice(0, 3).map((c, i) => ({ number: FOCUS_NUMBERS[i], ...c })),
    opportunities,
    evidence: buildEvidenceSummary(stats, ev),
    progress: buildProgressSummary(stats, ev),
    closing: { lines: closingFor(ctx) },
  };
  return { status: "ready", data };
}

function buildWatchingList(companies: HiringCompanyFact[]): string[] {
  const list = ["Your career graph and evidence profile"];
  if (companies[0]) {
    list.push(`${companies[0].name} hiring trend (${companies[0].open_positions_count} open roles)`);
  }
  list.push("New opportunities matching your skills");
  return list;
}

/** matched_skills holds {name, confidence} objects; the briefing shows names. */
function skillLabel(skill: unknown): string {
  if (skill && typeof skill === "object" && "name" in skill) return String((skill as { name: unknown }).name);
  return String(skill);
}

function mapOpportunity(o: OpportunityFact): Opportunity {
  const ex = o.explanation ?? {};
  const why = Array.isArray(ex.why)
    ? ex.why.slice(0, 2)
    : Array.isArray(ex.matched_skills)
      ? ex.matched_skills.slice(0, 2).map(skillLabel)
      : [];
  return {
    id: o.url,
    company: ex.company ?? hostFromUrl(o.url),
    role: ex.role ?? ex.title ?? "Open role",
    location: ex.location ?? "—",
    score: Math.round(o.career_score ?? 0),
    recommendation: (o.recommendation as Recommendation) ?? "CONSIDER",
    why,
    gap: o.skill_gaps.length > 0 ? o.skill_gaps[0] : undefined,
  };
}

function buildEvidenceSummary(stats: CareerGraphStats, ev: BriefingFacts["evidence"]): EvidenceSummary {
  const signals: EvidenceSignal[] = [];
  const projectCount = stats.projects_count ?? 0;
  const achievementCount = stats.achievements_count ?? 0;

  if (ev.skill_count > 0) signals.push({ text: `${ev.skill_count} skills mapped from your resume and profile` });
  if (projectCount > 0) signals.push({ text: `${projectCount} projects analyzed as evidence` });
  if (achievementCount > 0) signals.push({ text: `${achievementCount} achievements captured` });
  if (signals.length === 0) signals.push({ text: `${ev.total} evidence signals captured` });

  const avg = ev.avg_confidence;
  return { signalCount: ev.total, signals, confidence: avg >= 0.8 ? "High" : avg >= 0.6 ? "Medium" : "Low" };
}

function buildProgressSummary(stats: CareerGraphStats, ev: BriefingFacts["evidence"]): ProgressSummary {
  const { total, skill_count: skillCount } = ev;
  const projectCount = stats.projects_count ?? 0;

  let headline: string;
  let attribution: string;
  if (total >= 20) {
    headline = "Your career graph is rich and well-defined.";
    attribution = `Built from ${total} evidence signals across ${skillCount} skills and ${projectCount} projects.`;
  } else if (total >= 10) {
    headline = "Your career graph is gaining depth.";
    attribution = `${total} evidence signals and counting.`;
  } else if (total > 0) {
    headline = "Your career graph is taking shape.";
    attribution = `${total} signals captured — keep building your narrative.`;
  } else {
    headline = "Your career graph is starting to form.";
    attribution = "Add more evidence to strengthen your profile.";
  }

  return {
    headline,
    attribution,
    promise: "We'll keep measuring as you add more proof.",
    ctaLabel: "View career graph",
    ctaHref: "/onboarding?step=BUILDING",
  };
}

function hostFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "Opportunity";
  }
}
