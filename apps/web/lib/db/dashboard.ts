import { sql } from "./client";
import type {
  BriefingResult,
  BriefingData,
  BriefLine,
  FocusItem,
  Opportunity,
  Recommendation,
  EvidenceSummary,
  ProgressSummary,
  ClosingCopy,
  BriefingGreeting,
  EvidenceSignal,
} from "@/features/briefing/types";
import {
  type BriefingContext,
  type Tone,
  timeGreeting,
  greetingFor,
  subtitleFor,
  briefFor,
  closingFor,
  focusCandidates,
} from "@/lib/briefing/templates";

/**
 * Server-side briefing data layer.
 * Same direct-DB pattern as lib/db/onboarding.ts.
 * All reads run in parallel; assembly is pure and defensive.
 */
export async function getBriefingData(clerkId: string): Promise<BriefingResult> {
  const userQ = sql`SELECT profile_data FROM users WHERE clerk_id = ${clerkId} LIMIT 1`;

  const oppQ = sql`
    SELECT cs.url, cs.career_score, cs.recommendation, cs.skill_gaps, cs.explanation
    FROM career_scores cs
    JOIN (
      SELECT url, MAX(scanned_at) AS latest FROM career_scores
      WHERE user_id = ${clerkId} GROUP BY url
    ) latest ON cs.url = latest.url AND cs.scanned_at = latest.latest
    WHERE cs.user_id = ${clerkId} AND cs.recommendation IN ('APPLY', 'CONSIDER')
    ORDER BY cs.career_score DESC LIMIT 2
  `;

  const evidenceQ = sql`
    SELECT COUNT(*)::int AS total,
      COUNT(*) FILTER (WHERE evidence_data->>'type' = 'skill' OR evidence_data->>'type' IS NULL)::int AS skill_count,
      COALESCE(AVG(confidence_score), 0)::float AS avg_confidence
    FROM evidence_items WHERE user_id = ${clerkId}
  `;

  const companyQ = sql`
    SELECT name, hiring_trend, open_positions_count FROM companies
    WHERE hiring_trend IN ('up', 'spike') AND open_positions_count > 0
    ORDER BY open_positions_count DESC LIMIT 3
  `;

  // ── YENİ: 24 saatlik değişim (briefing'i "canlı" yapan) ──
  const deltaQ = sql`
    SELECT
      (SELECT COUNT(*) FROM evidence_items
        WHERE user_id = ${clerkId} AND created_at > NOW() - INTERVAL '24 hours')::int AS new_evidence,
      (SELECT COUNT(*) FROM career_scores
        WHERE user_id = ${clerkId} AND scanned_at > NOW() - INTERVAL '24 hours')::int AS new_scores
  `;

  // ── YENİ: gerçek hayat (interview/offer) ──
  const appsQ = sql`
    SELECT company, title, status FROM applications
    WHERE user_id = ${clerkId} AND status IN ('interview', 'offer') LIMIT 3
  `;

  const [user, opportunities, evidence, companies, delta, apps] = await Promise.all([
    userQ, oppQ, evidenceQ, companyQ, deltaQ, appsQ,
  ]);

  // Guarded yan sorgular — şema takılsa bile briefing ölmez
  let githubConnected = true;
  try {
    const gh = await sql`SELECT 1 FROM connected_accounts
      WHERE user_id = ${clerkId} AND provider = 'github' AND is_active = true LIMIT 1`;
    githubConnected = gh.length > 0;
  } catch { githubConnected = true; }

  let tone: Tone = "warm";
  try {
    const t = await sql`SELECT pref_metadata->>'communication_style' AS tone
      FROM career_preferences WHERE user_id = ${clerkId}`;
    const raw = t[0]?.tone;
    if (raw === "direct" || raw === "analytical") tone = raw;
  } catch { /* default warm */ }

  const profile = user[0]?.profile_data ?? {};
  const graphStats = (profile.career_graph ?? {}).stats ?? {};
  const ev = evidence[0] ?? { total: 0, skill_count: 0, avg_confidence: 0 };
  const firstName = profile.first_name ?? "there";
  const now = new Date();

  const hasEvidence = (ev.total ?? 0) > 0;
  const hasOpportunities = opportunities.length > 0;

  if (!hasEvidence && !hasOpportunities) {
    return {
      status: "empty",
      data: {
        greeting: timeGreeting(now.getHours()),
        watching: buildWatchingList(graphStats, companies),
        stats: {
          skills_count: graphStats.skills_count ?? ev.skill_count ?? 0,
          projects_count: graphStats.projects_count ?? 0,
          achievements_count: graphStats.achievements_count ?? 0,
          companies_count: graphStats.companies_count ?? 0,
        },
      },
    };
  }

  const ctx: BriefingContext = {
    hour: now.getHours(),
    dow: now.getDay(),
    skillCount: graphStats.skills_count ?? ev.skill_count ?? 0,
    projectCount: graphStats.projects_count ?? 0,
    achievementCount: graphStats.achievements_count ?? 0,
    opportunityCount: opportunities.length,
    topOpportunity: opportunities[0]
      ? { company: mapOpportunity(opportunities[0]).company, score: Math.round(opportunities[0].career_score ?? 0) }
      : null,
    hiringCompany: companies[0]
      ? { name: companies[0].name, openRoles: companies[0].open_positions_count }
      : null,
    newEvidence24h: delta[0]?.new_evidence ?? 0,
    newScores24h: delta[0]?.new_scores ?? 0,
    interviews: apps
      .filter((a: any) => a.status === "interview")
      .map((a: any) => ({ company: a.company, title: a.title })),
    offers: apps
      .filter((a: any) => a.status === "offer")
      .map((a: any) => ({ company: a.company, title: a.title })),
    githubConnected,
    tone,
  };

  const numbers = ["01", "02", "03"] as const;
  const data: BriefingData = {
    greeting: { name: firstName, greeting: greetingFor(ctx), subtitle: subtitleFor(ctx) },
    brief: briefFor(ctx),
    focus: focusCandidates(ctx).slice(0, 3).map((c, i) => ({ number: numbers[i], ...c })),
    opportunities: opportunities.map(mapOpportunity),
    evidence: buildEvidenceSummary(graphStats, ev),
    progress: buildProgressSummary(ev, graphStats),
    closing: { lines: closingFor(ctx) },
  };

  return { status: "ready", data };
}

// ─── Pure builders ─────────────────────────────────────────────────────────

function buildWatchingList(graphStats: any, companies: any[]): string[] {
  const list: string[] = ["Your career graph and evidence profile"];
  if (companies.length > 0) {
    list.push(`${companies[0].name} hiring trend (${companies[0].open_positions_count} open roles)`);
  }
  list.push("New opportunities matching your skills");
  return list;
}

function mapOpportunity(o: any): Opportunity {
  const explanation = o.explanation ?? {};
  return {
    id: o.url,
    company: explanation.company ?? hostFromUrl(o.url),
    role: explanation.role ?? explanation.title ?? "Open role",
    location: explanation.location ?? "—",
    score: Math.round(o.career_score ?? 0),
    recommendation: (o.recommendation as Recommendation) ?? "CONSIDER",
    why: Array.isArray(explanation.why)
      ? explanation.why.slice(0, 2)
      : Array.isArray(explanation.matched_skills)
        ? explanation.matched_skills.slice(0, 2)
        : [],
    gap: Array.isArray(o.skill_gaps) && o.skill_gaps.length > 0 ? o.skill_gaps[0] : undefined,
  };
}

function buildEvidenceSummary(graphStats: any, ev: any): EvidenceSummary {
  const avg = ev.avg_confidence ?? 0;

  const signals: EvidenceSignal[] = [];
  const skillCount = ev.skill_count ?? 0;
  const projectCount = graphStats.projects_count ?? 0;
  const achievementCount = graphStats.achievements_count ?? 0;

  if (skillCount > 0)
    signals.push({ text: `${skillCount} skills mapped from your resume and profile` });
  if (projectCount > 0) signals.push({ text: `${projectCount} projects analyzed as evidence` });
  if (achievementCount > 0) signals.push({ text: `${achievementCount} achievements captured` });

  if (signals.length === 0) {
    signals.push({ text: `${ev.total ?? 0} evidence signals captured` });
  }

  return {
    signalCount: ev.total ?? 0,
    signals,
    confidence: avg >= 0.8 ? "High" : avg >= 0.6 ? "Medium" : "Low",
  };
}

function buildProgressSummary(ev: any, graphStats: any): ProgressSummary {
  const total = ev.total ?? 0;
  const skillCount = ev.skill_count ?? 0;
  const projectCount = graphStats.projects_count ?? 0;

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
