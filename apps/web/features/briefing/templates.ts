import type { BriefLine, FocusItem } from "@/features/briefing/types";

export type Tone = "warm" | "direct" | "analytical";

export interface BriefingContext {
  hour: number;
  dow: number; // 0=Paz .. 6=Cmt
  skillCount: number;
  projectCount: number;
  achievementCount: number;
  opportunityCount: number;
  topOpportunity: { company: string; score: number } | null;
  hiringCompany: { name: string; openRoles: number } | null;
  newEvidence24h: number;
  newScores24h: number;
  interviews: Array<{ company: string; title: string }>;
  offers: Array<{ company: string; title: string }>;
  githubConnected: boolean;
  tone: Tone;
}

// ─── Tone vocabulary ────────────────────────────────────────────────────────
const TONE_PHRASES: Record<Tone, { quiet: string; signoff: string }> = {
  warm: {
    quiet: "Nothing changed since yesterday. Quiet days are part of the story too.",
    signoff: "That's your briefing for today.",
  },
  direct: {
    quiet: "No changes in 24h.",
    signoff: "End of briefing.",
  },
  analytical: {
    quiet: "Δ24h: 0 new signals. State stable.",
    signoff: "Summary complete.",
  },
};

// ─── Greeting ───────────────────────────────────────────────────────────────
export function timeGreeting(hour: number): string {
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function greetingFor(ctx: BriefingContext): string {
  return timeGreeting(ctx.hour);
}

// ─── Subtitle — priority: offer > interview > day > change > hiring ─────────
export function subtitleFor(ctx: BriefingContext): string | undefined {
  if (ctx.offers.length > 0)
    return `You have an offer from ${ctx.offers[0].company} — that changes everything.`;
  if (ctx.interviews.length > 0)
    return `${ctx.interviews[0].company} interview on your radar.`;
  if (ctx.dow === 1)
    return ctx.opportunityCount > 0
      ? `The week opens with ${ctx.opportunityCount} strong ${ctx.opportunityCount === 1 ? "match" : "matches"}.`
      : "A fresh week ahead.";
  if (ctx.dow === 5) return "Wrapping up the week.";
  if (ctx.newEvidence24h > 0 || ctx.newScores24h > 0)
    return "Things moved since yesterday.";
  if (ctx.hiringCompany)
    return `${ctx.hiringCompany.name} is hiring (${ctx.hiringCompany.openRoles} open roles).`;
  return undefined;
}

// ─── Brief lines — BLUF: change first ───────────────────────────────────────
export function briefFor(ctx: BriefingContext): BriefLine[] {
  const lines: BriefLine[] = [];
  const t = TONE_PHRASES[ctx.tone];

  if (ctx.newEvidence24h > 0) {
    lines.push({
      segments: [
        { text: `+${ctx.newEvidence24h} new ${ctx.newEvidence24h === 1 ? "signal" : "signals"}`, emphasis: "accent" },
        { text: " since yesterday." },
      ],
    });
  } else if (ctx.newScores24h > 0) {
    lines.push({
      segments: [
        { text: `${ctx.newScores24h} opportunities`, emphasis: "accent" },
        { text: " freshly scored overnight." },
      ],
    });
  }

  if (ctx.opportunityCount > 0 && ctx.topOpportunity) {
    lines.push({
      segments: [
        { text: ctx.topOpportunity.company, emphasis: "primary" },
        { text: ` leads your matches at ${ctx.topOpportunity.score}%.` },
      ],
    });
  } else if (ctx.skillCount > 0) {
    lines.push({
      segments: [
        { text: `${ctx.skillCount} skills`, emphasis: "success" },
        { text: " mapped in your career graph." },
      ],
    });
  }

  if (ctx.projectCount > 0)
    lines.push({
      segments: [
        { text: `${ctx.projectCount} projects`, emphasis: "success" },
        { text: " standing as evidence." },
      ],
    });

  if (ctx.achievementCount > 0)
    lines.push({
      segments: [
        { text: `${ctx.achievementCount} achievements`, emphasis: "accent" },
        { text: " — externally validated proof." },
      ],
    });

  if (lines.length === 0) lines.push({ segments: [{ text: t.quiet }] });
  lines.push({ segments: [{ text: t.signoff }], muted: true });
  return lines;
}

// ─── Focus — real life beats opportunities ──────────────────────────────────
export function focusCandidates(ctx: BriefingContext): Omit<FocusItem, "number">[] {
  const out: Omit<FocusItem, "number">[] = [];

  if (ctx.offers.length > 0) {
    out.push({
      action: `Review your offer from ${ctx.offers[0].company}`,
      reason: "The most time-sensitive item on your desk.",
      ctaLabel: "Review",
      ctaHref: "/applications",
    });
  } else if (ctx.interviews.length > 0) {
    out.push({
      action: `Prepare for ${ctx.interviews[0].company}`,
      reason: "An interview in your pipeline deserves today's energy.",
      ctaLabel: "Study plan",
      ctaHref: "/applications",
    });
  } else if (ctx.opportunityCount > 0 && ctx.topOpportunity) {
    out.push({
      action: `Review your top match — ${ctx.topOpportunity.company}`,
      reason: `Scored ${ctx.topOpportunity.score}% — strongest fit right now.`,
      ctaLabel: "Why strong?",
      ctaHref: "/inbox",
    });
  } else {
    out.push({
      action: "Run your first opportunity scan",
      reason: `${ctx.skillCount} skills mapped — ready to match against live roles.`,
      ctaLabel: "Scan now",
      ctaHref: "/inbox",
    });
  }

  if (!ctx.githubConnected)
    out.push({
      action: "Connect GitHub",
      reason: "Real code is your strongest evidence and raises skill confidence.",
      ctaLabel: "Connect",
      ctaHref: "/onboarding?step=CONNECTIONS",
    });

  out.push({
    action: "Review your extracted evidence",
    reason: "Precision beats volume — confirm every signal is accurate.",
    ctaLabel: "Review",
    ctaHref: "/onboarding?step=EVIDENCE",
  });

  return out;
}

// ─── Closing ────────────────────────────────────────────────────────────────
export function closingFor(ctx: BriefingContext): string[] {
  if (ctx.dow === 5)
    return ["That's everything important for this week.", "Enjoy your weekend. See you Monday."];
  if (ctx.dow === 0) return ["Rest well tonight.", "Tomorrow is a fresh start."];
  if (ctx.hour >= 22 || ctx.hour < 5)
    return ["That's everything for today.", "Rest well. We'll keep watching."];
  return ["That's everything important for today.", "We'll keep watching. See you tomorrow."];
}
