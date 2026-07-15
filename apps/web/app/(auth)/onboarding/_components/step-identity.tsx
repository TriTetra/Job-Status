"use client";

import { useState, type FormEvent, useEffect, useCallback, useMemo } from "react";
import { useUser } from "@clerk/nextjs";
import { onboardingApi, COUNTRIES, rolesApi } from "@/features/onboarding";
import { ROLES } from "@/features/onboarding/data/roles";
import { NarrativeText } from "@/components/shared/narrative-text";
import { SearchableCombobox, type ComboboxOption } from "@/components/shared/searchable-combobox";
import { Shield } from "lucide-react";

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
  };
  onComplete: () => void;
}

type CareerLevel = "junior" | "mid" | "senior" | "staff" | "principal";

function suggestCareerLevel(years: number): { level: CareerLevel; confidence: "low" | "medium" | "high" } {
  if (years < 2) return { level: "junior", confidence: "medium" };
  if (years < 5) return { level: "mid", confidence: "medium" };
  if (years < 10) return { level: "senior", confidence: "medium" };
  if (years < 15) return { level: "staff", confidence: "low" };
  return { level: "principal", confidence: "low" };
}

export function StepIdentity({ initialData, onComplete }: StepIdentityProps) {
  const { user } = useUser();

  const [firstName, setFirstName] = useState(initialData?.first_name || "");
  const [lastName, setLastName] = useState(initialData?.last_name || "");
  const [currentRoleId, setCurrentRoleId] = useState(initialData?.current_role_id || "");
  const [currentRoleTitle, setCurrentRoleTitle] = useState(initialData?.current_role_title || "");
  const [yearsInRole, setYearsInRole] = useState<number>(initialData?.years_in_role ?? 3);
  const [careerLevel, setCareerLevel] = useState<CareerLevel>(
    (initialData?.career_level as CareerLevel) || suggestCareerLevel(initialData?.years_in_role ?? 3).level
  );
  const [careerLevelOrigin, setCareerLevelOrigin] = useState<"user" | "system">("system");
  const [country, setCountry] = useState(initialData?.country || "");
  const [authorization, setAuthorization] = useState(initialData?.authorization || "authorized");

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

  // Sync with Clerk user details once loaded if empty
  useEffect(() => {
    if (user) {
      if (!firstName) setFirstName(user.firstName || "");
      if (!lastName) setLastName(user.lastName || "");
    }
  }, [user, firstName, lastName]);


  const isValid = firstName.trim().length > 0 && currentRoleId && country.length > 0;

  const suggestion = suggestCareerLevel(yearsInRole);

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
        authorization,
      });
      onComplete();
    } catch (err) {
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
          onChange={(id, title) => { setCurrentRoleId(id); setCurrentRoleTitle(title); }}
          placeholder="Search roles..."
          allowCustom={true}
          customLabel='Use "{query}" as my role'
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
          {(["junior", "mid", "senior", "staff", "principal"] as const).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => {
                setCareerLevel(level);
                setCareerLevelOrigin(level === suggestCareerLevel(yearsInRole).level ? "system" : "user");
              }}
              className={`flex-1 py-1.5 rounded-lg border text-[11px] font-semibold capitalize transition-all ${
                careerLevel === level
                  ? "border-[var(--accent)] bg-[rgba(255,177,98,0.05)] text-[var(--accent)]"
                  : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:border-[var(--border-strong)]"
              }`}
            >
              {level}
            </button>
          ))}
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

      {/* Work Authorization */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
          Work Authorization
        </label>
        <div className="grid grid-cols-2 gap-2">
          {([
            { val: "authorized", label: "Authorized", desc: "Citizen, PR, or valid visa" },
            { val: "sponsorship_required", label: "Needs Visa", desc: "Requires sponsorship" },
          ] as const).map(({ val, label, desc }) => (
            <div
              key={val}
              onClick={() => setAuthorization(val)}
              className="flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-all duration-200"
              style={{
                background: authorization === val ? "rgba(255,177,98,0.05)" : "var(--surface)",
                borderColor: authorization === val ? "var(--accent)" : "var(--border)",
              }}
            >
              <Shield className={`h-3.5 w-3.5 shrink-0 ${authorization === val ? "text-[var(--accent)]" : "text-[var(--text-muted)]"}`} />
              <div>
                <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{label}</div>
                <div className="text-[10px] leading-snug text-[var(--text-muted)]">{desc}</div>
              </div>
            </div>
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
