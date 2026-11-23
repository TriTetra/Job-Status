"use client";

import { Fragment, useEffect, useState, type ReactNode } from "react";
import { ArrowUpRight, Check, Loader2, Minus, X } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { formatScore, safeHttpUrl } from "@/lib/utils";
import { CompanyLogo } from "@/components/shared/company-logo";
import { ScoreRing } from "./score-ring";
import { tierOf } from "@/features/opportunities/tier";
import {
  CHANCE_COLOR, CHANCE_LABEL, DECISION_LABEL, SIZE_LABEL, SKIP_REASONS, TIER_COLOR, TIER_LABEL, type SkipReason,
  chanceOf, companyOf, postedAgo, salaryOf,
} from "@/features/opportunities/format";
import { getPosting, type Posting } from "@/features/opportunities/posting";
import type { Criterion, Opportunity } from "@/features/opportunities/types";
import { WhyModal } from "./why-modal";
import { PlaceBadge } from "./place-badge";
import { WhatPeopleSay } from "./what-people-say";

interface OpportunityDetailPanelProps {
  opp: Opportunity;
  onApply: () => void;
  onShortlist: () => void;
  /** "Not for me", with the one-tap reason the person picked (none for "Just skip"). */
  onSkip: (reasons: SkipReason[]) => void;
  busy?: boolean;
  /** Scored just now for a search, not saved: no deeper read (it needs a saved score). */
  scoredNow?: boolean;
}

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const SENIORITY: Record<string, string> = {
  intern: "Intern", junior: "Junior", mid: "Mid-level", senior: "Senior", staff: "Staff", principal: "Principal", manager: "Manager",
};

function CriterionIcon({ state }: { state: Criterion["state"] }) {
  if (state === "confirmed") return <Check className="h-3.5 w-3.5" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="matches" />;
  if (state === "conflict") return <X className="h-3.5 w-3.5" strokeWidth={2.5} style={{ color: "var(--danger)" }} aria-label="conflicts" />;
  return <Minus className="h-3.5 w-3.5" strokeWidth={2} style={{ color: "var(--text-muted)" }} aria-label="unknown" />;
}

const escapeRx = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Underline the skills you show (green) and the ones you don't (red) inside the posting text. */
function makeHighlighter(have: string[], missing: string[]) {
  {
    const terms = [...have.map((t) => [t, "have"] as const), ...missing.map((t) => [t, "miss"] as const)]
      .filter(([t]) => t.length >= 2)
      .sort((a, b) => b[0].length - a[0].length);
    if (!terms.length) return (text: string) => text as ReactNode;
    const kind = new Map(terms.map(([t, k]) => [t.toLowerCase(), k]));
    const rx = new RegExp(`(?<![\\w+#.])(${terms.map(([t]) => escapeRx(t)).join("|")})(?![\\w+#])`, "gi");
    return (text: string): ReactNode =>
      text.split(rx).map((part, i) => {
        const k = i % 2 === 1 ? kind.get(part.toLowerCase()) : undefined;
        if (!k) return <Fragment key={i}>{part}</Fragment>;
        const color = k === "have" ? "var(--success)" : "var(--danger)";
        return (
          <span key={i} className="font-medium" style={{ color: "var(--text-primary)", textDecoration: "underline", textDecorationColor: color,
                                                           textDecorationThickness: "2px", textUnderlineOffset: "4px" }}
                title={k === "have" ? "In your evidence" : "Not in your evidence"}>
            {part}
          </span>
        );
      });
  }
}

/**
 * The reader: the posting as an article on the left, your fit in the margin on the right —
 * score, chance, priorities, skills and the actions. Each side scrolls on its own.
 */
export function OpportunityDetailPanel({ opp, onApply, onShortlist, onSkip, busy, scoredNow }: OpportunityDetailPanelProps) {
  const [decision, setDecision] = useState(opp.decision);
  const [whyOpen, setWhyOpen] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState(false);
  const [posting, setPosting] = useState<Posting | null>(null);
  const [postingError, setPostingError] = useState(false);
  const [skipOpen, setSkipOpen] = useState(false);

  useEffect(() => {
    if (!skipOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setSkipOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [skipOpen]);

  const skip = (reasons: SkipReason[]) => {
    setSkipOpen(false);
    onSkip(reasons);
  };

  useEffect(() => {
    let live = true;
    getPosting(opp.url)
      .then((p) => live && setPosting(p))
      .catch(() => live && setPostingError(true));
    return () => {
      live = false;
    };
  }, [opp.url]);

  const ex = opp.explanation ?? {};
  const tier = tierOf(opp);
  const chance = chanceOf(opp);
  const status = opp.user_decision?.status ?? "unreviewed";
  const company = companyOf(opp);
  const companyKey = typeof ex.company_key === "string" ? ex.company_key : posting?.company_key ?? null;
  const postingUrl = safeHttpUrl(posting?.application_url) ?? safeHttpUrl(ex.application_url) ?? safeHttpUrl(opp.url);
  const have = (ex.matched_skills ?? []).map((m) => m.name);
  const gaps = opp.skill_gaps ?? [];
  const required = posting?.facts.required_skills ?? [];
  const haveSet = new Set(have.map((h) => h.toLowerCase()));
  const covered = required.filter((r) => haveSet.has(r.toLowerCase())).length;
  const highlight = makeHighlighter(have, gaps);
  const criteria = decision?.criteria ?? [];
  const reasoning = decision?.reasoning;
  const next = decision?.next_action;
  const f = posting?.facts;

  const chips = [
    salaryOf(opp),
    f?.seniority ? SENIORITY[f.seniority] ?? f.seniority : null,
    f?.min_years ? `${f.min_years}+ yrs` : null,
    f?.visa === "yes" ? "Sponsors visa" : f?.visa === "no" ? "No visa sponsorship" : null,
    postedAgo(opp) ? `Posted ${postedAgo(opp)}` : null,
    ex.company_size && SIZE_LABEL[ex.company_size] ? SIZE_LABEL[ex.company_size] : null,
  ].filter(Boolean) as string[];
  const trust = ex.trust;

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

  const quickWhy = have.length || gaps.length
    ? `${have.length ? `Your evidence covers ${have.slice(0, 3).join(", ")}` : "Few of its skills are in your evidence yet"}${gaps.length ? `; it also asks for ${gaps.slice(0, 2).join(" and ")}` : ""}.`
    : null;

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Masthead */}
      <header className="px-8 pt-7 pb-5 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-start gap-4">
          <CompanyLogo name={company} companyKey={companyKey} jobUrl={opp.url} size={52} />
          <div className="min-w-0 flex-1">
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {company}
              {DECISION_LABEL[status] && (
                <span className="ml-2 text-xs" style={{ color: status === "skipped" ? "var(--text-muted)" : "var(--accent)" }}>
                  · {DECISION_LABEL[status]}
                </span>
              )}
            </p>
            <h2 className="font-serif-display text-[28px] leading-tight mt-0.5" style={{ color: "var(--text-primary)" }}>
              {ex.title ?? posting?.title ?? "Open role"}
            </h2>
          </div>
        </div>
        <PlaceBadge ex={{ ...ex, workplace: ex.workplace ?? (f?.workplace === "remote" || f?.workplace === "hybrid" || f?.workplace === "onsite" ? f.workplace : null) }}
                    className="mt-4 text-sm" />
        {chips.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-x-2 gap-y-2">
            {chips.map((c) => (
              <li key={c} className="text-xs px-2.5 py-1 rounded-full border" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                {c}
              </li>
            ))}
          </ul>
        )}
      </header>

      {/* Article + margin */}
      <div className="flex-1 min-h-0 flex flex-col overflow-y-auto custom-scrollbar 2xl:grid 2xl:grid-cols-[minmax(0,1fr)_300px] 2xl:overflow-hidden">
        {/* The posting */}
        <article className="px-8 py-6 order-2 2xl:order-1 2xl:min-h-0 2xl:overflow-y-auto custom-scrollbar">
          {(f?.summary || ex.summary) && (
            <p className="font-editorial text-lg leading-relaxed mb-6" style={{ color: "var(--text-primary)" }}>
              {f?.summary || String(ex.summary)}
            </p>
          )}
          {posting === null && !postingError && (
            <div className="space-y-3" aria-busy="true">
              {[92, 100, 84, 96, 70, 88].map((w, i) => <div key={i} className="h-3.5 skeleton-shimmer rounded" style={{ width: `${w}%` }} />)}
            </div>
          )}
          {postingError && <p className="text-sm" style={{ color: "var(--text-muted)" }}>The posting text couldn&apos;t be loaded. Open it on the company&apos;s site.</p>}
          {posting && posting.blocks.length === 0 && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>This board doesn&apos;t share the posting text. Open it on the company&apos;s site.</p>
          )}
          {posting && posting.blocks.length > 0 && (
            <div className="max-w-[68ch] text-[15px] leading-7" style={{ color: "var(--text-secondary)" }}>
              {posting.blocks.map((b, i) =>
                b.type === "h" ? (
                  <h3 key={i} className="text-sm font-semibold mt-6 mb-2 first:mt-0" style={{ color: "var(--text-primary)" }}>{b.text}</h3>
                ) : b.type === "li" ? (
                  <p key={i} className="relative pl-5 my-1.5">
                    <span className="absolute left-1 top-[0.7em] h-1 w-1 rounded-full" style={{ background: "var(--accent)" }} />
                    {highlight(b.text)}
                  </p>
                ) : (
                  <p key={i} className="my-3">{highlight(b.text)}</p>
                ),
              )}
              {(have.length > 0 || gaps.length > 0) && (
                <p className="mt-8 text-xs flex flex-wrap gap-x-4" style={{ color: "var(--text-muted)" }}>
                  <span><span className="inline-block w-4 h-[2px] align-middle mr-1.5" style={{ background: "var(--success)" }} />in your evidence</span>
                  <span><span className="inline-block w-4 h-[2px] align-middle mr-1.5" style={{ background: "var(--danger)" }} />not in your evidence</span>
                </p>
              )}
            </div>
          )}
        </article>

        {/* Your fit, in the margin */}
        <aside className="px-8 2xl:px-6 py-6 border-b 2xl:border-b-0 2xl:border-l order-1 2xl:order-2 2xl:min-h-0 2xl:overflow-y-auto custom-scrollbar"
               style={{ borderColor: "var(--border)", background: "rgba(27,38,50,0.35)" }}>
          <div className="grid sm:grid-cols-[auto_minmax(0,1fr)] 2xl:grid-cols-1 gap-x-8 gap-y-6 items-center">
          <div className="flex items-center gap-4">
            <ScoreRing score={formatScore(opp.career_score)} color={TIER_COLOR[tier]} size={68} />
            <div>
              <p className="text-base font-semibold" style={{ color: TIER_COLOR[tier] }}>{TIER_LABEL[tier]}</p>
              <p className="text-sm" style={{ color: CHANCE_COLOR[chance] }}>{CHANCE_LABEL[chance]}</p>
              <button onClick={() => setWhyOpen(true)} className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                How it&apos;s calculated
              </button>
            </div>
          </div>

          <div className="space-y-2.5 2xl:mt-0">
            {postingUrl && (
              <a href={postingUrl} target="_blank" rel="noopener noreferrer" onClick={() => status === "unreviewed" && onShortlist()}
                 className="flex items-center justify-center gap-1.5 rounded-lg h-10 text-sm font-semibold w-full"
                 style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
                Open posting <ArrowUpRight className="h-4 w-4" strokeWidth={2} />
              </a>
            )}
            {posting?.via && safeHttpUrl(posting.via.url) && (
              <p className="text-center text-[11px]" style={{ color: "var(--text-muted)" }}>
                Found via{" "}
                <a href={safeHttpUrl(posting.via.url)!} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">
                  {posting.via.name}
                </a>
              </p>
            )}
            <div className="grid grid-cols-3 gap-2 text-xs">
              {[
                { label: status === "applied" ? "Applied ✓" : "I applied", on: onApply, off: status === "applied", color: "var(--text-primary)" },
                { label: status === "shortlisted" ? "Saved ✓" : "Shortlist", on: onShortlist, off: status === "shortlisted", color: "var(--text-secondary)" },
                { label: status === "skipped" ? "Skipped" : "Not for me", on: () => setSkipOpen((v) => !v), off: status === "skipped", color: "var(--text-muted)" },
              ].map((a) => (
                <button key={a.label} onClick={a.on} disabled={busy || a.off}
                        className="h-9 rounded-lg border disabled:opacity-50 transition-colors hover:bg-[var(--surface-hover)]"
                        style={{ borderColor: "var(--border)", color: a.color }}>
                  {a.label}
                </button>
              ))}
            </div>
            {skipOpen && (
              <div role="menu" aria-label="Why is it not for you?" className="menu-pop rounded-xl border p-1.5"
                   style={{ background: "var(--background)", borderColor: "var(--border-strong)" }}>
                <p className="px-2.5 pt-1 pb-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>Why not? Aplio learns from it.</p>
                {SKIP_REASONS.map((r) => (
                  <button key={r.id} role="menuitem" type="button" onClick={() => skip([r.id])} disabled={busy}
                          className="block w-full text-left text-sm px-2.5 py-1.5 rounded-md hover:bg-[var(--surface-hover)] disabled:opacity-50"
                          style={{ color: "var(--text-secondary)" }}>
                    {r.label}
                  </button>
                ))}
                <button role="menuitem" type="button" onClick={() => skip([])} disabled={busy}
                        className="block w-full text-left text-xs px-2.5 py-1.5 mt-0.5 rounded-md hover:bg-[var(--surface-hover)] disabled:opacity-50"
                        style={{ color: "var(--text-muted)" }}>
                  Just skip
                </button>
              </div>
            )}
          </div>

          </div>

          <div className="mt-7 grid md:grid-cols-2 2xl:grid-cols-1 gap-x-10 gap-y-7">
          <section>
            <p className={LABEL} style={LABEL_STYLE}>Why it could be worth it</p>
            {reasoning ? (
              <p className="font-editorial text-[15px] leading-relaxed mt-2" style={{ color: "var(--text-primary)" }}>{reasoning}</p>
            ) : (
              <>
                {quickWhy && <p className="text-sm leading-relaxed mt-2" style={{ color: "var(--text-secondary)" }}>{quickWhy}</p>}
                {scoredNow ? (
                  <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
                    Scored for this search, not one of your Opportunities. Shortlist it to keep it in Applications.
                  </p>
                ) : (
                <button onClick={explain} disabled={explaining} className="inline-flex items-center gap-1.5 text-xs mt-2" style={{ color: "var(--accent)" }}>
                  {explaining ? <><Loader2 className="h-3 w-3 animate-spin" /> Reading it against your evidence…</> : "Ask for a deeper read →"}
                </button>
                )}
              </>
            )}
            {explainError && <p className="mt-1 text-xs" role="alert" style={{ color: "var(--danger)" }}>Couldn&apos;t explain it right now.</p>}
            {next && <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}><span style={{ color: "var(--text-secondary)" }}>{next.label}.</span> {next.reason}</p>}
          </section>

          {required.length > 0 && (
            <section>
              <div className="flex items-baseline justify-between">
                <p className={LABEL} style={LABEL_STYLE}>Skills asked</p>
                <span className="font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{covered}/{required.length}</span>
              </div>
              <div className="mt-2 h-1 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                <div className="h-full rounded-full" style={{ width: `${(covered / required.length) * 100}%`, background: "var(--success)" }} />
              </div>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {required.map((s) => {
                  const ok = haveSet.has(s.toLowerCase());
                  return (
                    <li key={s} className="text-xs px-2 py-0.5 rounded-md border"
                        style={{ borderColor: ok ? "rgba(127,182,133,0.45)" : "rgba(201,106,90,0.45)", color: ok ? "var(--success)" : "var(--danger)" }}>
                      {s}
                    </li>
                  );
                })}
              </ul>
            </section>
          )}

          {trust && (trust.good.length > 0 || trust.concerns.length > 0) && (
            <section>
              <p className={LABEL} style={LABEL_STYLE}>About this employer</p>
              <ul className="mt-2 space-y-2">
                {trust.concerns.map((c) => (
                  <li key={c} className="grid grid-cols-[1rem_minmax(0,1fr)] gap-2 text-xs leading-relaxed">
                    <span className="pt-0.5"><CriterionIcon state="conflict" /></span>
                    <span style={{ color: trust.level === "risk" ? "var(--danger)" : "var(--text-secondary)" }}>{c}</span>
                  </li>
                ))}
                {trust.good.map((g) => (
                  <li key={g} className="grid grid-cols-[1rem_minmax(0,1fr)] gap-2 text-xs leading-relaxed">
                    <span className="pt-0.5"><CriterionIcon state="confirmed" /></span>
                    <span style={{ color: "var(--text-secondary)" }}>{g}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <WhatPeopleSay company={company} location={`${ex.location ?? ""} ${(ex.remote_regions ?? []).join(" ")}`} />

          {criteria.length > 0 && (
            <section>
              <p className={LABEL} style={LABEL_STYLE}>Your priorities</p>
              <ul className="mt-2 space-y-2">
                {criteria.map((c) => (
                  <li key={c.key} className="grid grid-cols-[1rem_minmax(0,1fr)] gap-2 text-xs leading-relaxed">
                    <span className="pt-0.5"><CriterionIcon state={c.state} /></span>
                    <span><span style={{ color: "var(--text-primary)" }}>{c.label}</span> <span style={{ color: "var(--text-muted)" }}>{c.detail}</span></span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          </div>

          {posting?.facts.read_by === "claude" && (
            <p className="mt-7 text-[11px]" style={{ color: "var(--text-muted)" }}>Facts read from the posting by Claude.</p>
          )}
        </aside>
      </div>

      {whyOpen && <WhyModal opp={{ ...opp, decision }} onClose={() => setWhyOpen(false)} />}
    </div>
  );
}
