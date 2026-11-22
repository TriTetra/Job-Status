"use client";

import { useEffect, useState } from "react";
import { settingsApi, type ScoringWeights } from "@/features/settings/api";
import { Section, Row, SaveBar } from "./kit";

const DEFAULTS: ScoringWeights = { fit: 0.3, acceptance: 0.25, career_value: 0.25, market_demand: 0.2 };

const META: { key: keyof ScoringWeights; label: string; hint: string; color: string }[] = [
  { key: "fit", label: "Skill match", hint: "How well your proof covers what the role asks", color: "#FFB162" },
  { key: "acceptance", label: "Chance of an offer", hint: "How realistic the role is for you", color: "#7FB685" },
  { key: "career_value", label: "Career value", hint: "The long-term step the move gives you", color: "#6BA5D7" },
  { key: "market_demand", label: "Market demand", hint: "How in-demand the role is right now", color: "#E6A817" },
];

/** Relative importance: the sliders don't have to add up — the scorer normalises them, and so does this view. */
export function ScoringTab() {
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    settingsApi
      .getWeights()
      .then((r) => setWeights({ ...DEFAULTS, ...r.weights }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const total = META.reduce((s, m) => s + (weights[m.key] ?? 0), 0);
  const share = (k: keyof ScoringWeights) => (total > 0 ? (weights[k] ?? 0) / total : 0);
  const isDefault = META.every((m) => Math.abs(share(m.key) - DEFAULTS[m.key]) < 0.005);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      // Store the normalised shares, so what you see is what is saved
      const normalised = Object.fromEntries(META.map((m) => [m.key, Math.round(share(m.key) * 1000) / 1000])) as unknown as ScoringWeights;
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
      <Section title="What matters most">
        <div className="mt-2 mb-2 flex h-2.5 rounded-full overflow-hidden gap-[2px]" aria-hidden="true">
          {META.map((m) => (
            <div key={m.key} className="h-full transition-all duration-300" style={{ width: `${share(m.key) * 100}%`, background: m.color }} />
          ))}
        </div>
        <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
          Move a slider to make that part count more. The shares always add up to 100%.
        </p>

        {META.map((m) => (
          <Row key={m.key} label={m.label} hint={m.hint}>
            <div className="flex items-center gap-4">
              <span className="h-2 w-2 rounded-full shrink-0" style={{ background: m.color }} />
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={weights[m.key]}
                aria-label={m.label}
                onChange={(e) => setWeights({ ...weights, [m.key]: parseFloat(e.target.value) })}
                className="flex-1 h-1 appearance-none rounded-full cursor-pointer"
                style={{ background: "var(--surface-hover)", accentColor: m.color }}
              />
              <span className="text-sm font-semibold tabular-nums w-12 text-right" style={{ color: m.color }}>
                {Math.round(share(m.key) * 100)}%
              </span>
            </div>
          </Row>
        ))}

        <div className="pt-4 flex items-center justify-between gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Saving re-ranks your opportunities on the next scan.</span>
          <button
            type="button"
            onClick={() => setWeights(DEFAULTS)}
            disabled={isDefault}
            className="underline underline-offset-4 disabled:opacity-40 disabled:no-underline cursor-pointer disabled:cursor-default"
          >
            Reset to defaults
          </button>
        </div>
        {total === 0 && (
          <p className="text-xs pt-2" style={{ color: "var(--danger)" }}>Give at least one part some weight.</p>
        )}
        {error && <p className="text-xs pt-2" style={{ color: "var(--danger)" }}>{error}</p>}
      </Section>

      <SaveBar onSave={handleSave} saving={saving} saved={saved} disabled={total === 0} />
    </div>
  );
}
