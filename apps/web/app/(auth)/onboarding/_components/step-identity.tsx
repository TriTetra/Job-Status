"use client";

import { useState, type FormEvent, useCallback, useMemo } from "react";
import { useMe } from "@/features/auth/use-me";
import { onboardingApi, COUNTRIES, rolesApi, SENIORITY, type SeniorityId } from "@/features/onboarding";
import { ROLES } from "@/features/onboarding/data/roles";
import { NarrativeText } from "@/components/shared/narrative-text";
import { SearchableCombobox, type ComboboxOption } from "@/components/shared/searchable-combobox";

interface StepIdentityProps {
  initialData?: {
    first_name?: string;
    last_name?: string;
    current_role_id?: string;
    current_role_title?: string;
    years_in_role?: number;
    career_level?: string;
    country?: string;
    authorization?: string;
    total_years?: number;
    languages?: Array<{ code: string; level: string }>;
    education_level?: string;
  };
  onComplete: () => void;
}

function suggestCareerLevel(years: number): { level: SeniorityId; confidence: "low" | "medium" | "high" } {
  if (years < 2)  return { level: "entry",  confidence: "medium" };
  if (years < 5)  return { level: "mid",    confidence: "medium" };
  if (years < 10) return { level: "senior", confidence: "medium" };
  if (years < 15) return { level: "lead",   confidence: "low" };
  return { level: "expert", confidence: "low" };
}

export function StepIdentity({ initialData, onComplete }: StepIdentityProps) {
  const me = useMe();

  const [firstName, setFirstName] = useState(initialData?.first_name || "");
  const [lastName, setLastName] = useState(initialData?.last_name || "");
  const [currentRoleId, setCurrentRoleId] = useState(initialData?.current_role_id || "");
  const [currentRoleTitle, setCurrentRoleTitle] = useState(initialData?.current_role_title || "");
  const [yearsInRole, setYearsInRole] = useState<number>(initialData?.years_in_role ?? 3);
  const [careerLevel, setCareerLevel] = useState<SeniorityId>(
    (initialData?.career_level as SeniorityId) || suggestCareerLevel(initialData?.years_in_role ?? 3).level
  );
  const [careerLevelOrigin, setCareerLevelOrigin] = useState<"user" | "system">("system");
  const [country, setCountry] = useState(initialData?.country || "");

  const [totalYears, setTotalYears] = useState<number>(
    initialData?.total_years ?? initialData?.years_in_role ?? 3
  );
  const [languages, setLanguages] = useState<Array<{ code: string; level: string }>>(
    initialData?.languages ?? []
  );
  const [educationLevel, setEducationLevel] = useState<string>(initialData?.education_level ?? "");

  const PROFICIENCY = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const countryOptions: ComboboxOption[] = useMemo(
    () => COUNTRIES.map((c) => ({ id: c.name, title: c.name, category: c.region })),
    []
  );

  const staticRoles: ComboboxOption[] = ROLES.map((r) => ({
    id: r.id,
    title: r.title,
    category: r.category,
    aliases: r.aliases,
  }));

  const handleRoleSearch = useCallback(async (query: string): Promise<ComboboxOption[]> => {
    const results = await rolesApi.search(query, 12);
    return results.map((r) => ({
      id: r.id,
      title: r.title,
      category: r.category,
      aliases: r.aliases,
      slug: r.slug,
    }));
  }, []);

  // Prefill empty name fields from the account once it has loaded
  const [prefilled, setPrefilled] = useState(false);
  if (me && !prefilled) {
    setPrefilled(true);
    if (!firstName) setFirstName(me.first_name || "");
    if (!lastName) setLastName(me.last_name || "");
  }


  const isValid = firstName.trim().length > 0 && currentRoleId && country.length > 0 && languages.length > 0;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isValid) return;

    setSaving(true);
    setError(null);

    try {
      await onboardingApi.saveIdentity({
        first_name: firstName,
        last_name: lastName || undefined,
        current_role_id: currentRoleId,
        current_role_title: currentRoleTitle,
        years_in_role: yearsInRole,
        career_level: careerLevel,
        career_level_origin: careerLevelOrigin,
        country,
        total_years: totalYears,
        languages,
        education_level: educationLevel || undefined,
      });
      onComplete();
    } catch (err) {
      console.error("[onboarding] save identity failed:", err);
      setSaving(false);
      setError("Failed to save. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Heading */}
      <div>
        <NarrativeText size="xl" weight="semibold">
          Tell us who you are.
        </NarrativeText>
      </div>

      {error && (
        <div className="p-2 bg-[rgba(235,94,85,0.1)] border border-[rgba(235,94,85,0.2)] rounded-lg text-xs text-[var(--danger)]">
          {error}
        </div>
      )}

      {/* Name */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
            First Name *
          </label>
          <input
            type="text"
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Abdullokh"
            className="w-full px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
            Last Name
          </label>
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Abdukodirov"
            className="w-full px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />
        </div>
      </div>

      {/* Current Role */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
          What best describes your work today? *
        </label>
        <SearchableCombobox
          initialOptions={staticRoles}
          onSearch={handleRoleSearch}
          value={currentRoleId}
          valueLabel={currentRoleTitle}
          onChange={(id, title) => { setCurrentRoleId(id); setCurrentRoleTitle(title); }}
          placeholder="Search roles..."
          allowCustom={true}
          customLabel='Use "{query}" as my role'
        />
      </div>

      {/* Total experience */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Total experience
          </label>
          <span className="text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded bg-[var(--surface-hover)] text-[var(--accent)] border border-[var(--border)]">
            {totalYears === 30 ? "30+" : `${totalYears}y`}
          </span>
        </div>
        <input
          type="range" min="0" max="30" step="1" value={totalYears}
          onChange={(e) => setTotalYears(Number(e.target.value))}
          className="w-full h-1 bg-[var(--surface-hover)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
        />
      </div>

      {/* Years in Role */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Years in this role
          </label>
          <span className="text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded bg-[var(--surface-hover)] text-[var(--accent)] border border-[var(--border)]">
            {yearsInRole === 25 ? "25+" : `${yearsInRole}y`}
          </span>
        </div>
        <input
          type="range"
          min="0" max="25" step="1"
          value={yearsInRole}
          onChange={(e) => {
            const years = Number(e.target.value);
            setYearsInRole(years);
            setCareerLevel(suggestCareerLevel(years).level);
            setCareerLevelOrigin("system");
          }}
          className="w-full h-1 bg-[var(--surface-hover)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
        />
      </div>

      {/* Career Level */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Career level
          </label>
          {yearsInRole > 0 && (
            <span className="text-[10px] text-[var(--text-muted)]">suggested · tap to override</span>
          )}
        </div>
        <div className="flex gap-1.5">
          {SENIORITY.map((lv) => {
            const active = careerLevel === lv.id;
            return (
              <button
                key={lv.id}
                type="button"
                onClick={() => {
                  setCareerLevel(lv.id);
                  setCareerLevelOrigin(lv.id === suggestCareerLevel(yearsInRole).level ? "system" : "user");
                }}
                className="group flex-1 py-1.5 rounded-lg border text-[11px] font-semibold transition-all duration-200"
                style={{
                  borderColor: active ? "var(--accent)" : "var(--border)",
                  background: active ? "rgba(255,177,98,0.05)" : "var(--surface)",
                  color: active ? "var(--accent)" : "var(--text-secondary)",
                  boxShadow: active ? "0 0 0 1px var(--accent), 0 4px 14px -6px rgba(255,177,98,0.5)" : "none",
                }}
              >
                {/* weight dots — the rung reads even without the word */}
                <span className="flex gap-0.5 justify-center mb-1">
                  {Array.from({ length: 5 }).map((_, di) => (
                    <span
                      key={di}
                      className="h-1 w-1 rounded-full transition-colors duration-200"
                      style={{
                        background:
                          di < lv.dots
                            ? active ? "var(--accent)" : "var(--text-muted)"
                            : "var(--border-strong)",
                      }}
                    />
                  ))}
                </span>
                {lv.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Country */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
          Country of Residence *
        </label>
        <SearchableCombobox
          initialOptions={countryOptions}
          value={country}
          onChange={(_id, title) => setCountry(title)}
          placeholder="Search countries..."
          allowCustom={false}
          emptyMessage="No country found"
        />
      </div>

      {/* Languages */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">
          Languages spoken *
        </label>
        <div className="flex flex-wrap gap-1.5">
          {languages.map((lang, i) => {
            const lvlIdx = PROFICIENCY.indexOf((lang.level as typeof PROFICIENCY[number]) || "A1");
            return (
              <span
                key={i}
                className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-xs animate-fade-in"
              >
                <input
                  value={lang.code}
                  onChange={(e) => setLanguages((p) => p.map((l, j) => (j === i ? { ...l, code: e.target.value } : l)))}
                  className="w-16 bg-transparent outline-none font-medium text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                  placeholder="Lang"
                />
                <span className="flex items-center gap-1">
                  {PROFICIENCY.map((lv, di) => (
                    <button
                      key={lv} type="button" title={lv}
                      onClick={() => setLanguages((p) => p.map((l, j) => (j === i ? { ...l, level: lv } : l)))}
                      className="h-1.5 w-1.5 rounded-full transition-all duration-150 hover:scale-150"
                      style={{ background: lvlIdx >= di ? "var(--accent)" : "var(--border-strong)" }}
                    />
                  ))}
                </span>
                <span className="text-[10px] font-mono text-[var(--text-muted)] w-5">{lang.level || "A1"}</span>
                <button
                  type="button"
                  onClick={() => setLanguages((p) => p.filter((_, j) => j !== i))}
                  className="text-[var(--text-muted)] hover:text-[var(--danger)] transition-colors leading-none"
                >×</button>
              </span>
            );
          })}
          <button
            type="button"
            onClick={() => setLanguages((p) => [...p, { code: "English", level: "C1" }])}
            className="inline-flex items-center px-2.5 py-1.5 rounded-full border border-dashed border-[var(--border)] text-xs text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors"
          >
            + Add language
          </button>
        </div>
      </div>

      {/* Education */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">
          Highest education
        </label>
        <div className="flex gap-1.5">
          {(["none", "bachelor", "master", "phd"] as const).map((lv) => (
            <button
              key={lv} type="button"
              onClick={() => setEducationLevel(lv)}
              className={`flex-1 py-1.5 rounded-lg border text-[11px] font-semibold capitalize transition-all ${
                educationLevel === lv
                  ? "border-[var(--accent)] bg-[rgba(255,177,98,0.05)] text-[var(--accent)]"
                  : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:border-[var(--border-strong)]"
              }`}
            >
              {lv}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={saving || !isValid}
        className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
        style={{
          background: !isValid || saving ? "var(--surface-hover)" : "var(--accent)",
          color: !isValid || saving ? "var(--text-muted)" : "var(--accent-fg)",
          cursor: !isValid || saving ? "not-allowed" : "pointer",
        }}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </form>
  );
}
