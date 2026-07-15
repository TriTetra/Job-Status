"use client";

import { useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi, GOALS, ROLES, COUNTRIES, CURRENCIES } from "@/features/onboarding";
import { ChipMultiSelect } from "./chip-multi-select";
import { SearchableMultiSelect } from "./searchable-multi-select";

interface StepGoalsProps {
  initialData?: {
    optimizing_for?: string[];
    preferred_roles?: string[];
    preferred_countries?: string[];
    salary_min?: number;
    salary_max?: number;
    salary_currency?: string;
  };
  onComplete: () => void;
}

export function StepGoals({ initialData, onComplete }: StepGoalsProps) {
  const [optimizingFor, setOptimizingFor] = useState<string[]>(
    initialData?.optimizing_for || []
  );
  const [roles, setRoles] = useState<string[]>(
    initialData?.preferred_roles || []
  );
  const [countries, setCountries] = useState<string[]>(
    initialData?.preferred_countries || []
  );
  const [salaryMin, setSalaryMin] = useState<string>(
    initialData?.salary_min?.toString() || ""
  );
  const [salaryMax, setSalaryMax] = useState<string>(
    initialData?.salary_max?.toString() || ""
  );
  const [currency, setCurrency] = useState<string>(
    initialData?.salary_currency || "EUR"
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid =
    optimizingFor.length >= 1 &&
    roles.length >= 1 &&
    countries.length >= 1;

  const handleSubmit = async () => {
    if (!isValid) return;

    setSaving(true);
    setError(null);

    try {
      await onboardingApi.saveGoals({
        optimizing_for: optimizingFor,
        preferred_roles: roles,
        preferred_countries: countries,
        salary_min: salaryMin ? parseInt(salaryMin) : undefined,
        salary_max: salaryMax ? parseInt(salaryMax) : undefined,
        salary_currency: salaryMin || salaryMax ? currency : undefined,
      });
      onComplete();
    } catch (e) {
      setError("Failed to save. Please try again.");
      setSaving(false);
    }
  };

  return (
    <div className="space-y-12">
      {/* ─── Narrative Opening ─── */}
      <div>
        <NarrativeText size="2xl" weight="semibold" className="mb-2">
          What are you optimizing for?
        </NarrativeText>
        <NarrativeText size="base" className="text-[var(--text-secondary)]">
          Pick up to 3. This shapes every recommendation Aplio makes.
        </NarrativeText>
      </div>

      {/* ─── Optimizing For (Emotional Goals) ─── */}
      <section>
        <ChipMultiSelect
          options={GOALS.map((g) => ({ id: g.id, label: g.label }))}
          selected={optimizingFor}
          onChange={setOptimizingFor}
          maxSelections={3}
          minSelections={1}
        />
      </section>

      {/* ─── Hairline Divider ─── */}
      <div className="h-px bg-[var(--border)]" />

      {/* ─── Roles ─── */}
      <section>
        <NarrativeText size="lg" weight="medium" className="mb-3">
          Preferred roles
        </NarrativeText>
        <SearchableMultiSelect
          options={ROLES.map((r) => ({ id: r.id, label: r.title }))}
          selected={roles}
          onChange={setRoles}
          maxSelections={5}
          minSelections={1}
          placeholder="Search roles..."
        />
      </section>

      {/* ─── Countries ─── */}
      <section>
        <NarrativeText size="lg" weight="medium" className="mb-3">
          Preferred countries
        </NarrativeText>
        <SearchableMultiSelect
          options={COUNTRIES.map((c) => ({ id: c.name, label: c.name }))}
          selected={countries}
          onChange={setCountries}
          maxSelections={5}
          minSelections={1}
          placeholder="Search countries..."
        />
      </section>

      {/* ─── Salary (Optional) ─── */}
      <section>
        <div className="flex items-baseline justify-between mb-3">
          <NarrativeText size="lg" weight="medium">
            Salary expectation
          </NarrativeText>
          <NarrativeText size="sm" className="text-[var(--text-muted)] italic">
            optional
          </NarrativeText>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="input-base w-24"
            disabled={!!saving}
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
            className="input-base flex-1"
            disabled={!!saving}
          />

          <span className="text-[var(--text-muted)]">—</span>

          <input
            type="number"
            value={salaryMax}
            onChange={(e) => setSalaryMax(e.target.value)}
            placeholder="Max"
            className="input-base flex-1"
            disabled={!!saving}
          />
        </div>
      </section>

      {/* ─── Error State ─── */}
      {error && (
        <NarrativeText size="sm" className="text-[var(--text-danger)]">
          {error}
        </NarrativeText>
      )}

      {/* ─── Submit Button ─── */}
      <div className="pt-4">
        <button
          onClick={handleSubmit}
          disabled={!isValid || saving}
          className="w-full h-12 bg-[var(--accent)] text-[var(--accent-fg)] font-medium rounded-md transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[var(--accent-hover)] active:scale-[0.98]"
        >
          {saving ? "Saving..." : "Continue"}
        </button>

        {!isValid && (
          <NarrativeText size="sm" className="text-[var(--text-muted)] mt-3 text-center">
            Select at least 1 goal, 1 role, and 1 country to continue.
          </NarrativeText>
        )}
      </div>

      <style jsx global>{`
        .input-base {
          height: 44px;
          padding: 0 14px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 10px;
          color: var(--text-primary);
          font-size: 14px;
          font-family: inherit;
          transition: border-color 150ms, background-color 150ms;
        }
        .input-base:hover:not(:disabled) {
          background: var(--surface-hover);
        }
        .input-base:focus {
          outline: none;
          border-color: var(--border-strong);
        }
        .input-base::placeholder {
          color: var(--text-muted);
        }
        .input-base:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
