"use client";

import { useEffect, useState } from "react";
import { settingsApi, type ScoringWeights } from "@/features/settings/api";
import { Section, Row, SaveBar } from "./kit";

const DEFAULTS: ScoringWeights = {
  fit: 0.3,
  acceptance: 0.25,
  career_value: 0.25,
  market_demand: 0.2,
};

const META: {
  key: keyof ScoringWeights;
  label: string;
  hint: string;
  color: string;
}[] = [
  {
    key: "fit",
    label: "Skill match",
    hint: "How well your evidence covers the role",
    color: "#FFB162",
  },
  {
    key: "acceptance",
    label: "Acceptance",
    hint: "Realistic chance of an offer",
    color: "#7FB685",
  },
  {
    key: "career_value",
    label: "Career value",
    hint: "Long-term growth this move adds",
    color: "#6BA5D7",
  },
  {
    key: "market_demand",
    label: "Market demand",
    hint: "How hot the role is right now",
    color: "#E6A817",
  },
];

export function ScoringTab() {
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    settingsApi
      .getWeights()
      .then((r) => setWeights({ ...DEFAULTS, ...r.weights }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const total = META.reduce((s, m) => s + (weights[m.key] ?? 0), 0);
  const valid = Math.abs(total - 1) < 0.011;

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await settingsApi.saveWeights(weights);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <p className="text-sm py-8" style={{ color: "var(--text-muted)" }}>
        Loading…
      </p>
    );
  }

  return (
    <div>
      <Section title="Weight distribution">
        {/* NYT-style stacked bar — no chart library */}
        <div
          className="flex h-2 rounded-full overflow-hidden mb-6"
          style={{ background: "var(--surface-hover)" }}
        >
          {META.map((m) => (
            <div
              key={m.key}
              className="h-full transition-all duration-300"
              style={{ width: `${(weights[m.key] ?? 0) * 100}%`, background: m.color }}
            />
          ))}
        </div>

        {META.map((m) => (
          <Row key={m.key} label={m.label} hint={m.hint}>
            <div className="flex items-center gap-4">
              <span
                className="h-2 w-2 rounded-full shrink-0"
                style={{ background: m.color }}
              />
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={weights[m.key]}
                onChange={(e) =>
                  setWeights({ ...weights, [m.key]: parseFloat(e.target.value) })
                }
                className="flex-1 h-1 appearance-none rounded-full cursor-pointer"
                style={{ background: "var(--surface-hover)", accentColor: m.color }}
              />
              <span
                className="text-sm font-semibold tabular-nums w-12 text-right"
                style={{ color: m.color }}
              >
                {Math.round((weights[m.key] ?? 0) * 100)}%
              </span>
            </div>
          </Row>
        ))}

        <div className="py-4 flex items-center justify-between text-sm">
          <span style={{ color: "var(--text-muted)" }}>Total</span>
          <span
            className="font-semibold tabular-nums"
            style={{ color: valid ? "var(--success)" : "var(--danger)" }}
          >
            {Math.round(total * 100)}%
          </span>
        </div>
        {!valid && (
          <p className="text-xs pb-2" style={{ color: "var(--danger)" }}>
            Weights must add up to 100%.
          </p>
        )}
      </Section>

      <SaveBar onSave={handleSave} saving={saving} saved={saved} disabled={!valid} />
    </div>
  );
}
