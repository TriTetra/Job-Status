"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { formatScore } from "@/lib/utils";
import type { Opportunity, ScoreModel } from "@/features/opportunities/types";

interface WhyModalProps {
  opp: Opportunity;
  onClose: () => void;
}

const pct = (x: number, digits = 1) => `${(x * 100).toFixed(x < 0.1 ? digits : 0)}%`;

const FACTOR_LABEL: Record<string, string> = {
  skills: "Skills they ask for",
  title: "Your target roles vs this title",
  experience: "Experience asked",
  timing: "How fresh the posting is",
  competition: "How many will apply",
  location: "Where it is, for you",
  agency: "Posted by an agency",
};
const VALUE_LABEL: Record<string, string> = { pay: "Pay", growth: "Growth", stability: "Stability", work_style: "Work style" };

function factorNote(key: string, m: ScoreModel): string {
  const f = m.chance_factors;
  if (key === "skills") return `you show ${pct(f.must_coverage)} of the must-haves`;
  if (key === "experience") return f.experience_note || "within range";
  if (key === "location") return f.location_note || "";
  if (key === "competition") return f.competition < 0.5 ? "open to many countries: crowded" : f.competition < 1 ? "remote or well known" : "";
  if (key === "timing") return f.timing < 1 ? "older posting" : "posted in the last few days";
  return "";
}

/** "How it's calculated": the v8 model in plain words — chance × how much the job beats your bar. */
export function WhyModal({ opp, onClose }: WhyModalProps) {
  const m = opp.explanation?.model;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 settings-scrim" onClick={onClose} aria-hidden="true" />
      <div role="dialog" aria-modal="true" aria-labelledby="why-title"
           className="settings-panel relative w-full max-w-[560px] max-h-[88dvh] overflow-y-auto custom-scrollbar rounded-2xl border p-7"
           style={{ background: "var(--background)", borderColor: "var(--border-strong)", boxShadow: "0 40px 120px rgba(0,0,0,0.55)" }}>
        <button onClick={onClose} aria-label="Close" className="absolute top-5 right-5 h-8 w-8 rounded-md flex items-center justify-center hover:bg-[var(--surface)]"
                style={{ color: "var(--text-muted)" }}>
          <X className="h-4 w-4" />
        </button>
        <h2 id="why-title" className="font-serif-display text-[26px] leading-tight" style={{ color: "var(--text-primary)" }}>
          Why {opp.career_score != null ? formatScore(opp.career_score) : "this score"}?
        </h2>

        {!m ? (
          <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
            This job was scored before the current model. It will be explained here after the next refresh.
          </p>
        ) : (
          <>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              The score weighs your <b style={{ color: "var(--text-primary)" }}>chance of an interview</b> against{" "}
              <b style={{ color: "var(--text-primary)" }}>how good the job would be for you</b>. A long shot has to be much better to rank
              high, because every application costs you time.
            </p>

            {m.gates.length > 0 && (
              <div className="mt-5 rounded-lg border p-3 text-sm" style={{ borderColor: "rgba(201,106,90,0.5)", color: "var(--danger)" }}>
                {m.gates.map((g) => <p key={g}>✕ {g}</p>)}
              </div>
            )}

            <section className="mt-6">
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Chance of an interview</p>
                <p className="font-serif-display text-2xl tabular-nums" style={{ color: "var(--text-primary)" }}>{pct(m.p_effective)}</p>
              </div>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                A cold application starts around 8%, then each of these multiplies it:
              </p>
              <ul className="mt-3 space-y-2">
                {Object.entries(FACTOR_LABEL).map(([key, label]) => {
                  const v = m.chance_factors[key as keyof ScoreModel["chance_factors"]];
                  if (typeof v !== "number" || (key === "agency" && v === 1)) return null;
                  const note = factorNote(key, m);
                  return (
                    <li key={key} className="grid grid-cols-[minmax(0,1fr)_3.5rem] gap-3 text-sm">
                      <span style={{ color: "var(--text-secondary)" }}>
                        {label}{note && <span style={{ color: "var(--text-muted)" }}> · {note}</span>}
                      </span>
                      <span className="font-mono text-xs tabular-nums text-right"
                            style={{ color: v >= 0.95 ? "var(--success)" : v >= 0.5 ? "var(--text-secondary)" : "var(--danger)" }}>
                        ×{v.toFixed(2)}
                      </span>
                    </li>
                  );
                })}
                <li className="grid grid-cols-[minmax(0,1fr)_3.5rem] gap-3 text-sm">
                  <span style={{ color: "var(--text-secondary)" }}>The posting is real <span style={{ color: "var(--text-muted)" }}>· older ones are often filled</span></span>
                  <span className="font-mono text-xs tabular-nums text-right" style={{ color: "var(--text-secondary)" }}>×{m.p_real.toFixed(2)}</span>
                </li>
              </ul>
            </section>

            <section className="mt-6">
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Value if you get it</p>
                <p className="font-serif-display text-2xl tabular-nums" style={{ color: "var(--text-primary)" }}>{Math.round(m.value * 100)}</p>
              </div>
              <ul className="mt-3 space-y-2">
                {Object.entries(VALUE_LABEL).map(([key, label]) => {
                  const v = m.value_parts[key];
                  if (typeof v !== "number") return null;  // flags like below_minimum are shown below
                  return (
                    <li key={key} className="grid grid-cols-[6rem_minmax(0,1fr)_2.5rem] items-center gap-3 text-sm">
                      <span style={{ color: "var(--text-secondary)" }}>{label}</span>
                      <span className="h-1.5 rounded-full" style={{ background: "rgba(238,233,223,0.08)" }}>
                        <span className="block h-full rounded-full" style={{ width: `${v * 100}%`, background: "var(--accent)" }} />
                      </span>
                      <span className="font-mono text-xs tabular-nums text-right" style={{ color: "var(--text-muted)" }}>{Math.round(v * 100)}</span>
                    </li>
                  );
                })}
              </ul>
              {m.value_parts.below_minimum && (
                <p className="mt-2 text-xs" style={{ color: "var(--danger)" }}>Pay is below your minimum, so value is capped.</p>
              )}
            </section>

            <p className="mt-6 text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
              Method: hard limits first (visa rules, language, scams), then chance × value as in Bied et al. (2026), with
              factors anchored on hiring research. Weights for pay, growth, stability and work style, and how much effort an
              application costs you, are in Settings → Scoring. The factors are estimates until Aplio learns from your own
              applications.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
