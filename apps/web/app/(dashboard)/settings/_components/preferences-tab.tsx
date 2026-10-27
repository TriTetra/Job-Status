"use client";

import { useEffect, useState } from "react";
import { settingsApi } from "@/features/settings/api";
import { COUNTRIES, CURRENCIES } from "@/features/onboarding/constants";
import { SearchableMultiSelect } from "@/app/(auth)/onboarding/_components/searchable-multi-select";
import { Section, Row, CheckRow, RadioRow, Pill, UnderlineInput, SaveBar } from "./kit";

type Tone = "warm" | "direct" | "analytical";

export function PreferencesTab() {
  const [loading, setLoading] = useState(true);
  const [workArr, setWorkArr] = useState<string[]>([]);
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [sponsorship, setSponsorship] = useState<boolean | null>(null);
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [period, setPeriod] = useState<"year" | "month">("year");
  const [tone, setTone] = useState<Tone>("warm");

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    settingsApi
      .getPreferences()
      .then((p) => {
        setWorkArr(p.work_arrangements ?? []);
        setCountryCodes(p.preferred_country_codes ?? []);
        setSponsorship(p.requires_sponsorship ?? null);
        setSalaryMin(p.salary?.min?.toString() ?? "");
        setSalaryMax(p.salary?.max?.toString() ?? "");
        setCurrency(p.salary?.currency ?? "USD");
        setPeriod(p.salary?.period === "month" ? "month" : "year");
        const t = p.pref_metadata?.communication_style;
        if (t === "direct" || t === "analytical") setTone(t);
      })
      .catch(() => setError("Could not load preferences."))
      .finally(() => setLoading(false));
  }, []);

  const salaryError =
    salaryMin && salaryMax && parseInt(salaryMin) > parseInt(salaryMax)
      ? "Min cannot exceed max"
      : null;

  const toggle = (list: string[], set: (v: string[]) => void, id: string) =>
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await settingsApi.patchPreferences({
        work_arrangements: workArr,
        preferred_country_codes: countryCodes,
        requires_sponsorship: sponsorship,
        salary_min: salaryMin ? parseInt(salaryMin) : null,
        salary_max: salaryMax ? parseInt(salaryMax) : null,
        salary_currency: currency,
        salary_period: period,
        pref_metadata: { communication_style: tone },
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Failed to save. Please try again.");
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
      <Section title="Work arrangement">
        <CheckRow
          checked={workArr.includes("remote")}
          onChange={() => toggle(workArr, setWorkArr, "remote")}
          label="Remote"
          hint="Work from anywhere"
        />
        <CheckRow
          checked={workArr.includes("hybrid")}
          onChange={() => toggle(workArr, setWorkArr, "hybrid")}
          label="Hybrid"
          hint="Mix of office and remote"
        />
        <CheckRow
          checked={workArr.includes("onsite")}
          onChange={() => toggle(workArr, setWorkArr, "onsite")}
          label="On-site"
          hint="Required for clinical, field, studio and on-prem roles"
        />
      </Section>

      <Section title="Target locations">
        <div className="space-y-3">
          <div className="flex justify-between items-center mb-1">
            <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
              Preferred countries
            </label>
            <span className="text-[10px] text-[var(--text-muted)]">{countryCodes.length}/5</span>
          </div>
          <SearchableMultiSelect
            options={COUNTRIES.map((c) => ({ id: c.code, label: c.name }))}
            selected={countryCodes}
            onChange={setCountryCodes}
            maxSelections={5}
            minSelections={0}
            placeholder="Search countries..."
          />
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            We&apos;ll prioritize opportunities in these markets.
          </p>
        </div>
      </Section>

      <Section title="Visa sponsorship">
        <RadioRow
          checked={sponsorship === false}
          onSelect={() => setSponsorship(false)}
          label="No sponsorship needed"
          hint="Work permit ready"
        />
        <RadioRow
          checked={sponsorship === true}
          onSelect={() => setSponsorship(true)}
          label="Require sponsorship"
          hint="Only show roles offering visa support"
        />
      </Section>

      <Section title="Salary expectation">
        <Row label="Range" hint={salaryError ?? "Used to filter out under-paying roles"}>
          <div className="flex items-center gap-3">
            <UnderlineInput
              type="number"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              placeholder="Min"
              className="md:max-w-[110px]"
            />
            <span className="text-sm" style={{ color: "var(--text-muted)" }}>
              —
            </span>
            <UnderlineInput
              type="number"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              placeholder="Max"
              className="md:max-w-[110px]"
            />
          </div>
        </Row>
        <Row label="Currency & period">
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="bg-transparent border-0 border-b border-[var(--border)] focus:border-[var(--accent)] outline-none py-1 text-sm cursor-pointer"
              style={{ color: "var(--text-primary)" }}
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c} style={{ background: "var(--surface)" }}>
                  {c}
                </option>
              ))}
            </select>
            <Pill active={period === "year"} onClick={() => setPeriod("year")}>
              / yr
            </Pill>
            <Pill active={period === "month"} onClick={() => setPeriod("month")}>
              / mo
            </Pill>
          </div>
        </Row>
      </Section>

      <Section title="Briefing voice">
        <RadioRow
          checked={tone === "warm"}
          onSelect={() => setTone("warm")}
          label="Warm"
          hint="A quiet colleague who knows you well"
        />
        <RadioRow
          checked={tone === "direct"}
          onSelect={() => setTone("direct")}
          label="Direct"
          hint="Numbers first, no small talk"
        />
        <RadioRow
          checked={tone === "analytical"}
          onSelect={() => setTone("analytical")}
          label="Analytical"
          hint="Deltas and distributions"
        />
      </Section>

      {error && (
        <p className="text-xs mt-4" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      <SaveBar onSave={handleSave} saving={saving} saved={saved} disabled={!!salaryError} />
    </div>
  );
}
