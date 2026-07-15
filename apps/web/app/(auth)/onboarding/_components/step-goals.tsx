"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi } from "@/features/onboarding";
import { rolesApi, type Role } from "@/features/onboarding/api/roles";
import { COUNTRIES, CURRENCIES } from "@/features/onboarding/constants";
import { SearchableMultiSelect } from "./searchable-multi-select";
import { Check } from "lucide-react";

// ─── Flat goal list — no categories, no emoji ─────────────────────────────────
const GOALS = [
  { id: "technical_depth", label: "Technical Depth" },
  { id: "leadership",      label: "Leadership"       },
  { id: "remote_first",    label: "Remote First"     },
  { id: "balance",         label: "Work-Life Balance" },
  { id: "high_salary",     label: "High Compensation" },
  { id: "startup",         label: "Startup"          },
  { id: "big_tech",        label: "Big Tech"         },
  { id: "mission",         label: "Mission Driven"   },
  { id: "innovation",      label: "Innovation"       },
  { id: "open_source",     label: "Open Source"      },
] as const;

const WORK_ARRANGEMENTS = [
  { id: "remote",  label: "Remote"  },
  { id: "hybrid",  label: "Hybrid"  },
  { id: "onsite",  label: "On-site" },
] as const;

interface StepGoalsProps {
  initialData?: {
    goal_ids?: string[];
    preferred_role_ids?: string[];
    preferred_country_codes?: string[];
    work_arrangements?: string[];
    salary?: {
      min?: number;
      max?: number;
      currency?: string;
      period?: string;
      negotiable?: boolean;
    };
  };
  onComplete: () => void;
}

export function StepGoals({ initialData, onComplete }: StepGoalsProps) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);

  useEffect(() => {
    rolesApi.getAll().then(setRoles).catch(console.error).finally(() => setRolesLoading(false));
  }, []);

  const [goalIds,       setGoalIds]       = useState<string[]>(initialData?.goal_ids ?? []);
  const [roleIds,       setRoleIds]       = useState<string[]>(initialData?.preferred_role_ids ?? []);
  const [countryCodes,  setCountryCodes]  = useState<string[]>(initialData?.preferred_country_codes ?? []);
  const [workArr,       setWorkArr]       = useState<string[]>(initialData?.work_arrangements ?? []);
  const [salaryMin,     setSalaryMin]     = useState(initialData?.salary?.min?.toString() ?? "");
  const [salaryMax,     setSalaryMax]     = useState(initialData?.salary?.max?.toString() ?? "");
  const [currency,      setCurrency]      = useState(initialData?.salary?.currency ?? "EUR");
  const [saving,        setSaving]        = useState(false);
  const [error,         setError]         = useState<string | null>(null);

  const salaryError = useMemo(() => {
    if (!salaryMin && !salaryMax) return null;
    const mn = parseInt(salaryMin), mx = parseInt(salaryMax);
    if (!isNaN(mn) && !isNaN(mx) && mn > mx) return "Min cannot exceed max";
    return null;
  }, [salaryMin, salaryMax]);

  const isValid =
    goalIds.length >= 1 &&
    roleIds.length >= 1 &&
    countryCodes.length >= 1 &&
    workArr.length >= 1 &&
    !salaryError;

  const toggleGoal = useCallback((id: string) => {
    setGoalIds((prev) =>
      prev.includes(id)
        ? prev.filter((g) => g !== id)
        : prev.length < 3 ? [...prev, id] : prev
    );
  }, []);

  const handleSubmit = async () => {
    if (!isValid) return;
    setSaving(true);
    setError(null);
    try {
      await onboardingApi.saveGoals({
        goal_ids: goalIds,
        preferred_role_ids: roleIds,
        preferred_country_codes: countryCodes,
        work_arrangements: workArr,
        salary_min: salaryMin ? parseInt(salaryMin) : undefined,
        salary_max: salaryMax ? parseInt(salaryMax) : undefined,
        salary_currency: salaryMin || salaryMax ? currency : undefined,
        salary_period: "year",
        salary_negotiable: true,
      });
      onComplete();
    } catch {
      setError("Failed to save. Please try again.");
      setSaving(false);
    }
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-3">
      {/* Heading */}
      <div>
        <NarrativeText size="xl" weight="semibold">
          Where do you want to go?
        </NarrativeText>
      </div>

      {error && (
        <div className="p-2 bg-[rgba(235,94,85,0.1)] border border-[rgba(235,94,85,0.2)] rounded-lg text-xs text-[var(--danger)]">
          {error}
        </div>
      )}

      {/* ─── Goals ─── */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Optimizing for *
          </label>
          <span className="text-[10px] text-[var(--text-muted)]">{goalIds.length}/3</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {GOALS.map(({ id, label }) => {
            const isSelected = goalIds.includes(id);
            const disabled   = !isSelected && goalIds.length >= 3;
            return (
              <button
                key={id}
                type="button"
                onClick={() => toggleGoal(id)}
                disabled={disabled}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                  isSelected
                    ? "border-[var(--accent)] bg-[rgba(255,177,98,0.05)] text-[var(--accent)]"
                    : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:border-[var(--border-strong)]"
                } ${disabled ? "opacity-35 cursor-not-allowed" : "cursor-pointer"}`}
              >
                {isSelected && <Check className="h-3 w-3" strokeWidth={2.5} />}
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── Target Roles ─── */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Target roles *
          </label>
          <span className="text-[10px] text-[var(--text-muted)]">{roleIds.length}/5</span>
        </div>
        {rolesLoading ? (
          <div className="h-9 bg-[var(--surface)] rounded-lg animate-pulse" />
        ) : (
          <SearchableMultiSelect
            options={roles.map((r) => ({ id: r.id, label: r.title }))}
            selected={roleIds}
            onChange={setRoleIds}
            maxSelections={5}
            minSelections={1}
            placeholder="Search roles..."
          />
        )}
      </div>

      {/* ─── Target Locations ─── */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Target locations *
          </label>
          <span className="text-[10px] text-[var(--text-muted)]">{countryCodes.length}/5</span>
        </div>
        <SearchableMultiSelect
          options={COUNTRIES.map((c) => ({ id: c.code, label: c.name }))}
          selected={countryCodes}
          onChange={setCountryCodes}
          maxSelections={5}
          minSelections={1}
          placeholder="Search countries..."
        />
      </div>

      {/* ─── Work Arrangement ─── */}
      <div>
        <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]">
          Work arrangement *
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          {WORK_ARRANGEMENTS.map(({ id, label }) => {
            const isSelected = workArr.includes(id);
            return (
              <button
                key={id}
                type="button"
                onClick={() => {
                  if (isSelected) {
                    if (workArr.length > 1) setWorkArr(workArr.filter((a) => a !== id));
                  } else {
                    setWorkArr([...workArr, id]);
                  }
                }}
                className={`py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  isSelected
                    ? "border-[var(--accent)] bg-[rgba(255,177,98,0.05)] text-[var(--accent)]"
                    : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:border-[var(--border-strong)]"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── Salary (optional) ─── */}
      <div>
        <div className="flex items-baseline justify-between mb-1">
          <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Salary expectation
          </label>
          <span className="text-[10px] italic text-[var(--text-muted)]">optional</span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="w-20 px-2 py-1.5 rounded-lg border text-xs outline-none transition-colors"
            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input
            type="number"
            value={salaryMin}
            onChange={(e) => setSalaryMin(e.target.value)}
            placeholder="Min"
            className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />
          <span className="text-[var(--text-muted)] text-sm">—</span>
          <input
            type="number"
            value={salaryMax}
            onChange={(e) => setSalaryMax(e.target.value)}
            placeholder="Max"
            className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />
        </div>
        {salaryError && (
          <p className="text-[10px] text-[var(--danger)] mt-1">{salaryError}</p>
        )}
      </div>

      {/* ─── Submit ─── */}
      <button
        type="submit"
        disabled={saving || !isValid}
        className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
        style={{
          background: !isValid || saving ? "var(--surface-hover)" : "var(--accent)",
          color:      !isValid || saving ? "var(--text-muted)"    : "var(--accent-fg)",
          cursor:     !isValid || saving ? "not-allowed"          : "pointer",
        }}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </form>
  );
}
