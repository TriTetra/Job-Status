"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi } from "@/features/onboarding";
import { rolesApi, type Role } from "@/features/onboarding/api/roles";
import {
  GOAL_CATEGORIES,
  TOTAL_GOALS_LIMIT,
  WORK_ARRANGEMENTS,
  COUNTRIES,
  CURRENCIES,
} from "@/features/onboarding/constants";
import { SearchableMultiSelect } from "./searchable-multi-select";
import { Check, Plus } from "lucide-react";

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
  // ─── Roles from API ───────────────────────────────────────────────────────
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);

  useEffect(() => {
    rolesApi
      .getAll()
      .then(setRoles)
      .catch(console.error)
      .finally(() => setRolesLoading(false));
  }, []);

  // ─── Form state ───────────────────────────────────────────────────────────
  const [goalIds, setGoalIds] = useState<string[]>(initialData?.goal_ids ?? []);
  const [roleIds, setRoleIds] = useState<string[]>(initialData?.preferred_role_ids ?? []);
  const [countryCodes, setCountryCodes] = useState<string[]>(
    initialData?.preferred_country_codes ?? []
  );
  const [workArrangements, setWorkArrangements] = useState<string[]>(
    initialData?.work_arrangements ?? []
  );
  const [salaryMin, setSalaryMin] = useState(initialData?.salary?.min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = useState(initialData?.salary?.max?.toString() ?? "");
  const [currency, setCurrency] = useState(initialData?.salary?.currency ?? "EUR");
  const [salaryPeriod, setSalaryPeriod] = useState(initialData?.salary?.period ?? "year");
  const [negotiable, setNegotiable] = useState(initialData?.salary?.negotiable ?? true);
  const [showSalary, setShowSalary] = useState(!!initialData?.salary?.min);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── Salary validation ────────────────────────────────────────────────────
  const salaryError = useMemo(() => {
    if (!showSalary || (!salaryMin && !salaryMax)) return null;
    const min = parseInt(salaryMin);
    const max = parseInt(salaryMax);
    if (salaryMin && isNaN(min)) return "Invalid min salary";
    if (salaryMax && isNaN(max)) return "Invalid max salary";
    if (!isNaN(min) && !isNaN(max) && min > max) return "Min cannot exceed max";
    return null;
  }, [showSalary, salaryMin, salaryMax]);

  const isValid =
    goalIds.length >= 1 &&
    roleIds.length >= 1 &&
    countryCodes.length >= 1 &&
    workArrangements.length >= 1 &&
    !salaryError;

  // ─── Category-aware goal management ──────────────────────────────────────
  const getGoalsInCategory = useCallback(
    (categoryName: string) => {
      const cat = GOAL_CATEGORIES.find((c) => c.name === categoryName);
      if (!cat) return [];
      const catIds = new Set(cat.goals.map((g) => g.id));
      return goalIds.filter((id) => catIds.has(id));
    },
    [goalIds]
  );

  const toggleGoal = useCallback(
    (categoryName: string, goalId: string) => {
      const cat = GOAL_CATEGORIES.find((c) => c.name === categoryName);
      if (!cat) return;
      const catIds = new Set(cat.goals.map((g) => g.id));
      const selectedInCat = goalIds.filter((id) => catIds.has(id));
      const isSelected = goalIds.includes(goalId);

      if (isSelected) {
        setGoalIds(goalIds.filter((id) => id !== goalId));
      } else {
        if (selectedInCat.length >= cat.maxSelections || goalIds.length >= TOTAL_GOALS_LIMIT)
          return;
        setGoalIds([...goalIds, goalId]);
      }
    },
    [goalIds]
  );

  // ─── Submit ───────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!isValid) return;
    setSaving(true);
    setError(null);
    try {
      await onboardingApi.saveGoals({
        goal_ids: goalIds,
        preferred_role_ids: roleIds,
        preferred_country_codes: countryCodes,
        work_arrangements: workArrangements,
        salary_min: showSalary && salaryMin ? parseInt(salaryMin) : undefined,
        salary_max: showSalary && salaryMax ? parseInt(salaryMax) : undefined,
        salary_currency: showSalary ? currency : undefined,
        salary_period: showSalary ? salaryPeriod : undefined,
        salary_negotiable: showSalary ? negotiable : undefined,
      });
      onComplete();
    } catch {
      setError("Failed to save. Please try again.");
      setSaving(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <NarrativeText size="xl" weight="semibold" className="mb-1">
          Where do you want to go?
        </NarrativeText>
        <NarrativeText size="sm" className="text-[var(--text-secondary)]">
          This shapes every recommendation Aplio makes.
        </NarrativeText>
      </div>

      {error && (
        <div className="p-2.5 bg-[rgba(235,94,85,0.1)] border border-[rgba(235,94,85,0.2)] rounded-lg text-xs text-[var(--danger)]">
          {error}
        </div>
      )}

      {/* ─── Goals ─── */}
      <section>
        <div className="flex items-baseline justify-between mb-2">
          <label className="text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            What are you optimizing for?
          </label>
          <span className="text-[11px] text-[var(--text-muted)]">
            {goalIds.length}/{TOTAL_GOALS_LIMIT}
          </span>
        </div>

        <div className="space-y-2.5">
          {GOAL_CATEGORIES.map((category) => {
            const selectedInCat = getGoalsInCategory(category.name);
            return (
              <div key={category.name}>
                <div className="text-[10px] text-[var(--text-muted)] mb-1 uppercase tracking-wider">
                  {category.name}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {category.goals.map((goal) => {
                    const isSelected = goalIds.includes(goal.id);
                    const disabled =
                      !isSelected &&
                      (selectedInCat.length >= category.maxSelections ||
                        goalIds.length >= TOTAL_GOALS_LIMIT);
                    return (
                      <button
                        key={goal.id}
                        type="button"
                        onClick={() => toggleGoal(category.name, goal.id)}
                        disabled={disabled}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all border"
                        style={{
                          background: isSelected ? "rgba(255,177,98,0.15)" : "var(--surface)",
                          color: isSelected ? "var(--accent)" : "var(--text-secondary)",
                          borderColor: isSelected ? "rgba(255,177,98,0.3)" : "var(--border)",
                          opacity: disabled ? 0.35 : 1,
                          cursor: disabled ? "not-allowed" : "pointer",
                        }}
                      >
                        {isSelected && <Check className="h-3 w-3" strokeWidth={2.5} />}
                        <span>{goal.icon}</span>
                        <span>{goal.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="h-px bg-[var(--border)]" />

      {/* ─── Target Roles ─── */}
      <section>
        <div className="flex items-baseline justify-between mb-2">
          <label className="text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Target roles
          </label>
          <span className="text-[11px] text-[var(--text-muted)]">{roleIds.length}/5</span>
        </div>
        {rolesLoading ? (
          <div className="h-10 bg-[var(--surface)] rounded-lg animate-pulse" />
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
      </section>

      {/* ─── Target Locations ─── */}
      <section>
        <div className="flex items-baseline justify-between mb-2">
          <label className="text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
            Target locations
          </label>
          <span className="text-[11px] text-[var(--text-muted)]">{countryCodes.length}/5</span>
        </div>
        <SearchableMultiSelect
          options={COUNTRIES.map((c) => ({ id: c.code, label: c.name }))}
          selected={countryCodes}
          onChange={setCountryCodes}
          maxSelections={5}
          minSelections={1}
          placeholder="Search countries..."
        />
      </section>

      {/* ─── Work Arrangement ─── */}
      <section>
        <label className="block text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)] mb-2">
          Work arrangement
        </label>
        <div className="flex gap-2">
          {WORK_ARRANGEMENTS.map((arr) => {
            const isSelected = workArrangements.includes(arr.id);
            return (
              <button
                key={arr.id}
                type="button"
                onClick={() => {
                  if (isSelected) {
                    if (workArrangements.length > 1)
                      setWorkArrangements(workArrangements.filter((a) => a !== arr.id));
                  } else {
                    setWorkArrangements([...workArrangements, arr.id]);
                  }
                }}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg border text-sm font-medium transition-all"
                style={{
                  background: isSelected ? "rgba(255,177,98,0.08)" : "var(--surface)",
                  color: isSelected ? "var(--accent)" : "var(--text-secondary)",
                  borderColor: isSelected ? "var(--accent)" : "var(--border)",
                }}
              >
                <span>{arr.icon}</span>
                <span>{arr.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      <div className="h-px bg-[var(--border)]" />

      {/* ─── Compensation (progressive disclosure) ─── */}
      <section>
        {!showSalary ? (
          <button
            type="button"
            onClick={() => setShowSalary(true)}
            className="flex items-center gap-1.5 text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
          >
            <Plus className="h-4 w-4" strokeWidth={2} />
            Add compensation preference
            <span className="text-[var(--text-muted)] text-xs">(optional)</span>
          </button>
        ) : (
          <div className="space-y-2.5">
            <div className="flex items-baseline justify-between">
              <label className="text-[11px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
                Compensation
              </label>
              <button
                type="button"
                onClick={() => { setShowSalary(false); setSalaryMin(""); setSalaryMax(""); }}
                className="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
              >
                Remove
              </button>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="input-compact w-20"
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <input
                type="number"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
                placeholder="Min"
                className="input-compact flex-1"
              />
              <span className="text-[var(--text-muted)] text-sm">—</span>
              <input
                type="number"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
                placeholder="Max"
                className="input-compact flex-1"
              />
              <select
                value={salaryPeriod}
                onChange={(e) => setSalaryPeriod(e.target.value)}
                className="input-compact w-20"
              >
                <option value="year">/yr</option>
                <option value="month">/mo</option>
              </select>
            </div>
            {salaryError && (
              <p className="text-[10px] text-[var(--danger)]">{salaryError}</p>
            )}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={negotiable}
                onChange={(e) => setNegotiable(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              <span className="text-xs text-[var(--text-secondary)]">Open to negotiation</span>
            </label>
          </div>
        )}
      </section>

      {/* ─── Submit ─── */}
      <div className="pt-1">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!isValid || saving}
          className="w-full py-2.5 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
          style={{
            background: !isValid || saving ? "var(--surface-hover)" : "var(--accent)",
            color: !isValid || saving ? "var(--text-muted)" : "var(--accent-fg)",
            cursor: !isValid || saving ? "not-allowed" : "pointer",
          }}
        >
          {saving ? "Saving…" : "Continue"}
        </button>
        {!isValid && !salaryError && (
          <p className="text-[10px] text-[var(--text-muted)] mt-2 text-center">
            Select at least 1 goal · 1 role · 1 location · 1 work arrangement
          </p>
        )}
      </div>

      <style jsx global>{`
        .input-compact {
          height: 36px;
          padding: 0 10px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 8px;
          color: var(--text-primary);
          font-size: 13px;
          font-family: inherit;
          transition: border-color 150ms;
        }
        .input-compact:focus {
          outline: none;
          border-color: var(--accent);
        }
        .input-compact::placeholder {
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
