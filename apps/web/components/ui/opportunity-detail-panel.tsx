"use client";

import { useState } from "react";
import { ArrowUpRight, Check, Loader2, Minus, X } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { formatScore, safeHttpUrl } from "@/lib/utils";
import { tierOf } from "@/features/opportunities/tier";
import {
  CHANCE_COLOR, CHANCE_LABEL, DECISION_LABEL, TIER_COLOR, TIER_LABEL,
  chanceOf, companyOf, postedAgo, salaryOf, whereOf,
} from "@/features/opportunities/format";
import type { Criterion, Opportunity } from "@/features/opportunities/types";
import { WhyModal } from "./why-modal";

interface OpportunityDetailPanelProps {
  opp: Opportunity;
  onApply: () => void;
  onShortlist: () => void;
  onSkip: () => void;
  busy?: boolean;
}

const LABEL = "text-[11px] uppercase tracking-[0.08em] mb-3";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

function CriterionIcon({ state }: { state: Criterion["state"] }) {
  if (state === "confirmed") return <Check className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="matches" />;
  if (state === "conflict") return <X className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--danger)" }} aria-label="conflicts" />;
  return <Minus className="h-4 w-4" strokeWidth={2} style={{ color: "var(--text-muted)" }} aria-label="unknown" />;
}

/**
 * The decision surface: who and what, the facts, why it fits, what it asks that you
 * don't show yet, and one clear next step. Hairlines, no boxes.
 */
export function OpportunityDetailPanel({ opp, onApply, onShortlist, onSkip, busy }: OpportunityDetailPanelProps) {
  const [decision, setDecision] = useState(opp.decision);
  const [whyOpen, setWhyOpen] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState(false);

  const ex = opp.explanation ?? {};
  const tier = tierOf(opp);
  const chance = chanceOf(opp);
  const status = opp.user_decision?.status ?? "unreviewed";
  const postingUrl = safeHttpUrl(ex.application_url) ?? safeHttpUrl(opp.url);
  const meta = [whereOf(opp), salaryOf(opp), postedAgo(opp) && `posted ${postedAgo(opp)}`,
    ex.source && ex.source !== "unknown" ? `via ${ex.source}` : null].filter(Boolean).join(" · ");
  const matched = ex.matched_skills ?? [];
  const gaps = opp.skill_gaps ?? [];
  const criteria = decision?.criteria ?? [];
  const reasoning = decision?.reasoning;
  const next = decision?.next_action;

  const explain = async () => {
    setExplaining(true);
    setExplainError(false);
    try {
      const res = await apiFetch<{ decision: NonNullable<Opportunity["decision"]> }>(
        `/api/jobs/reasoning/${encodeURIComponent(opp.url)}`,
      );
      setDecision(res.decision);
    } catch {
      setExplainError(true);
    } finally {
      setExplaining(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-8">
      {/* Who and what */}
      <div className="flex items-baseline justify-between gap-4">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{companyOf(opp)}</p>
        {DECISION_LABEL[status] && (
          <span className="text-xs" style={{ color: status === "skipped" ? "var(--text-muted)" : "var(--accent)" }}>
            {DECISION_LABEL[status]}
          </span>
        )}
      </div>
      <h2 className="font-serif-display text-3xl leading-tight mt-1" style={{ color: "var(--text-primary)" }}>
        {ex.title ?? "Open role"}
      </h2>
      {meta && <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>{meta}</p>}

      {/* Verdict line */}
      <div className="mt-5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-mono text-2xl font-semibold tabular-nums" style={{ color: TIER_COLOR[tier] }}>
          {formatScore(opp.career_score)}
        </span>
        <span className="text-sm font-medium" style={{ color: TIER_COLOR[tier] }}>{TIER_LABEL[tier]}</span>
        <span className="text-sm" style={{ color: CHANCE_COLOR[chance] }}>· {CHANCE_LABEL[chance]}</span>
        <button onClick={() => setWhyOpen(true)} className="ml-auto text-xs" style={{ color: "var(--text-muted)" }}>
          How is {formatScore(opp.career_score)} calculated?
        </button>
      </div>

      {typeof ex.summary === "string" && ex.summary && (
        <p className="mt-5 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{ex.summary}</p>
      )}

      {/* Why */}
      <section className="mt-7 pt-6 border-t" style={{ borderColor: "var(--border)" }}>
        <div className={LABEL} style={LABEL_STYLE}>Why it could be worth it</div>
        {reasoning ? (
          <p className="font-editorial text-lg leading-relaxed" style={{ color: "var(--text-primary)" }}>{reasoning}</p>
        ) : (
          <button onClick={explain} disabled={explaining} className="inline-flex items-center gap-2 text-sm"
                  style={{ color: "var(--accent)" }}>
            {explaining ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Reading the posting against your evidence…</> : "Explain this match →"}
          </button>
        )}
        {explainError && <p className="mt-2 text-xs" role="alert" style={{ color: "var(--danger)" }}>Couldn&apos;t explain it right now.</p>}
      </section>

      {/* Against your priorities */}
      {criteria.length > 0 && (
        <section className="mt-7 pt-6 border-t" style={{ borderColor: "var(--border)" }}>
          <div className={LABEL} style={LABEL_STYLE}>Against your priorities</div>
          <ul className="space-y-2.5">
            {criteria.map((c) => (
              <li key={c.key} className="grid grid-cols-[1.25rem_minmax(0,1fr)] gap-2">
                <span className="pt-0.5"><CriterionIcon state={c.state} /></span>
                <span className="text-sm">
                  <span style={{ color: "var(--text-primary)" }}>{c.label}</span>
                  <span style={{ color: "var(--text-muted)" }}> — {c.detail}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Skills */}
      {(matched.length > 0 || gaps.length > 0) && (
        <section className="mt-7 pt-6 border-t space-y-3" style={{ borderColor: "var(--border)" }}>
          {matched.length > 0 && (
            <p className="text-sm leading-relaxed">
              <span style={LABEL_STYLE} className="text-[11px] uppercase tracking-[0.08em] mr-2">You show</span>
              <span style={{ color: "var(--success)" }}>{matched.map((m) => m.name).join(" · ")}</span>
            </p>
          )}
          {gaps.length > 0 && (
            <p className="text-sm leading-relaxed">
              <span style={LABEL_STYLE} className="text-[11px] uppercase tracking-[0.08em] mr-2">They ask, you don&apos;t show</span>
              <span style={{ color: "var(--danger)" }}>{gaps.slice(0, 8).join(" · ")}</span>
            </p>
          )}
        </section>
      )}

      {/* Next step + actions */}
      <section className="mt-7 pt-6 border-t" style={{ borderColor: "var(--border)" }}>
        {next && (
          <p className="text-sm mb-5" style={{ color: "var(--text-secondary)" }}>
            <span className="font-medium" style={{ color: "var(--text-primary)" }}>{next.label}.</span> {next.reason}
          </p>
        )}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
          {postingUrl && (
            <a href={postingUrl} target="_blank" rel="noopener noreferrer" onClick={() => status === "unreviewed" && onShortlist()}
               className="inline-flex items-center gap-1.5 rounded-md px-4 h-10 text-sm font-semibold"
               style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              Open posting <ArrowUpRight className="h-4 w-4" strokeWidth={2} />
            </a>
          )}
          <button onClick={onApply} disabled={busy || status === "applied"} className="text-sm disabled:opacity-50"
                  style={{ color: "var(--text-primary)" }}>
            {status === "applied" ? "Applied ✓" : "I applied"}
          </button>
          <button onClick={onShortlist} disabled={busy || status === "shortlisted"} className="text-sm disabled:opacity-50"
                  style={{ color: "var(--text-secondary)" }}>
            {status === "shortlisted" ? "Shortlisted ✓" : "Shortlist"}
          </button>
          <button onClick={onSkip} disabled={busy || status === "skipped"} className="text-sm disabled:opacity-50"
                  style={{ color: "var(--text-muted)" }}>
            {status === "skipped" ? "Skipped" : "Not for me"}
          </button>
        </div>
        {postingUrl && status === "unreviewed" && (
          <p className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
            Opening the posting also shortlists it, so it&apos;s in Applications when you come back.
          </p>
        )}
      </section>

      {whyOpen && <WhyModal opp={{ ...opp, decision }} onClose={() => setWhyOpen(false)} />}
    </div>
  );
}
