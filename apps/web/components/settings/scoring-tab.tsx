"use client";

import { useEffect, useState } from "react";
import { settingsApi, type ScoringWeights } from "@/features/settings/api";
import { Section, Row, RadioRow, SaveBar } from "./kit";

type ValueKey = "pay" | "growth" | "stability" | "work_style";

const DEFAULTS: ScoringWeights = { pay: 0.35, growth: 0.22, stability: 0.18, work_style: 0.13, effort: 2 };

const META: { key: ValueKey; label: string; hint: string; color: string }[] = [
  { key: "pay", label: "Pay", hint: "Against your minimum, or what similar roles pay there", color: "#FFB162" },
  { key: "growth", label: "Growth", hint: "What you'd learn, the step up, the employer's scale", color: "#6BA5D7" },
  { key: "stability", label: "Stability", hint: "How likely the company is to be around and hiring", color: "#7FB685" },
  { key: "work_style", label: "Work style", hint: "Remote, hybrid or on-site, as you prefer", color: "#E6A817" },
];

const EFFORT = [
  { value: 1, label: "Quick", hint: "One-click applications: long shots are still worth a try" },
  { value: 2, label: "Normal", hint: "A short note for each: balanced" },
  { value: 3, label: "Tailored", hint: "A tailored CV for each: only apply where your chance is real" },
];

/** What a good job means to you (value), and how much an application costs you (the bar for long shots). */
export function ScoringTab() {
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    settingsApi
      .getWeights()
      .then((r) => {
        const w = r.weights as Partial<ScoringWeights>;
        setWeights({
          pay: w.pay ?? DEFAULTS.pay, growth: w.growth ?? DEFAULTS.growth, stability: w.stability ?? DEFAULTS.stability,
          work_style: w.work_style ?? DEFAULTS.work_style, effort: w.effort ?? DEFAULTS.effort,
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const total = META.reduce((s, m) => s + (weights[m.key] ?? 0), 0);
  const share = (k: ValueKey) => (total > 0 ? (weights[k] ?? 0) / total : 0);
  const isDefault = META.every((m) => Math.abs(share(m.key) - DEFAULTS[m.key]) < 0.01) && weights.effort === DEFAULTS.effort;

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const normalised = {
        ...Object.fromEntries(META.map((m) => [m.key, Math.round(share(m.key) * 1000) / 1000])),
        effort: weights.effort,
      } as ScoringWeights;
      await settingsApi.saveWeights(normalised);
      setWeights(normalised);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-sm py-8" style={{ color: "var(--text-muted)" }}>Loading…</p>;

  return (
    <div>
      <Section title="How the score works">
        <p className="text-sm leading-relaxed py-2" style={{ color: "var(--text-secondary)" }}>
          Each role gets a <b style={{ color: "var(--text-primary)" }}>chance of an interview</b> (your skills against what they ask,
          your experience, how fresh and how crowded the posting is, and whether you can legally take it from where you live) and a{" "}
          <b style={{ color: "var(--text-primary)" }}>value</b>{" "}if you get it. They are combined so a long shot has to be much better to
          rank high. Roles you can&apos;t take (a visa they rule out, a language you don&apos;t have, scam signs) are set aside.
        </p>
      </Section>

      <Section title="What a good job means to you">
        <div className="mt-2 mb-2 flex h-2.5 rounded-full overflow-hidden gap-[2px]" aria-hidden="true">
          {META.map((m) => (
            <div key={m.key} className="h-full transition-all duration-300" style={{ width: `${share(m.key) * 100}%`, background: m.color }} />
          ))}
        </div>
        {META.map((m) => (
          <Row key={m.key} label={m.label} hint={m.hint}>
            <div className="flex items-center gap-4">
              <span className="h-2 w-2 rounded-full shrink-0" style={{ background: m.color }} />
              <input type="range" min={0} max={1} step={0.05} value={weights[m.key]} aria-label={m.label}
                     onChange={(e) => setWeights({ ...weights, [m.key]: parseFloat(e.target.value) })}
                     className="flex-1 h-1 appearance-none rounded-full cursor-pointer"
                     style={{ background: "var(--surface-hover)", accentColor: m.color }} />
              <span className="text-sm font-semibold tabular-nums w-12 text-right" style={{ color: m.color }}>
                {Math.round(share(m.key) * 100)}%
              </span>
            </div>
          </Row>
        ))}
      </Section>

      <Section title="How much effort is one application?">
        {EFFORT.map((e) => (
          <RadioRow key={e.value} checked={weights.effort === e.value} onSelect={() => setWeights({ ...weights, effort: e.value })}
                    label={e.label} hint={e.hint} />
        ))}
        <div className="pt-4 flex items-center justify-between gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Saving re-ranks your opportunities on the next refresh.</span>
          <button type="button" onClick={() => setWeights(DEFAULTS)} disabled={isDefault}
                  className="underline underline-offset-4 disabled:opacity-40 disabled:no-underline cursor-pointer disabled:cursor-default">
            Reset to defaults
          </button>
        </div>
        {total === 0 && <p className="text-xs pt-2" style={{ color: "var(--danger)" }}>Give at least one part some weight.</p>}
        {error && <p className="text-xs pt-2" style={{ color: "var(--danger)" }}>{error}</p>}
      </Section>

      <SaveBar onSave={handleSave} saving={saving} saved={saved} disabled={total === 0} />
    </div>
  );
}
