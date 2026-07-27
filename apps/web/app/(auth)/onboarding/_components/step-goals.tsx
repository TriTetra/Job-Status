"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { AplioLogo } from "@/components/shared/aplio-logo";
import { onboardingApi, STEP_ORDER, SENIORITY, type SeniorityId } from "@/features/onboarding";
import { rolesApi, type Role } from "@/features/onboarding/api/roles";
import { COUNTRIES, CURRENCIES } from "@/features/onboarding/constants";
import { SearchableMultiSelect } from "./searchable-multi-select";
import { Check, ShieldCheck, Stamp, Sparkles } from "lucide-react";

interface GoalItem { id: string; label: string; theme: string; suggested: boolean }

const WORK_ARRANGEMENTS = [
  { id: "remote", label: "Remote" },
  { id: "hybrid", label: "Hybrid" },
  { id: "onsite", label: "On-site" },
] as const;

interface StepGoalsProps {
  initialData?: {
    goal_ids?: string[];
    preferred_role_ids?: string[];
    preferred_country_codes?: string[];
    work_arrangements?: string[];
    requires_sponsorship?: boolean;
    contract_types?: string[];
    availability?: string | null;
    target_seniority?: string | null;
    salary?: { min?: number; max?: number; currency?: string; period?: string; negotiable?: boolean };
  };
  onComplete: () => void;
}

export function StepGoals({ initialData, onComplete }: StepGoalsProps) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);
  const [catalog, setCatalog] = useState<GoalItem[]>([]);
  const [roleTitle, setRoleTitle] = useState<string | null>(null);

  useEffect(() => {
    rolesApi.getAll().then(setRoles).catch(console.error).finally(() => setRolesLoading(false));
    onboardingApi
      .getGoalCatalog()
      .then((c) => { setCatalog(c.goals); setRoleTitle(c.role_title); })
      .catch(console.error);
  }, []);

  const [goalIds, setGoalIds] = useState<string[]>(initialData?.goal_ids ?? []);
  const [roleIds, setRoleIds] = useState<string[]>(initialData?.preferred_role_ids ?? []);
  const [countryCodes, setCountryCodes] = useState<string[]>(initialData?.preferred_country_codes ?? []);
  const [workArr, setWorkArr] = useState<string[]>(initialData?.work_arrangements ?? []);
  const [sponsorship, setSponsorship] = useState<"none" | "needed" | null>(
    initialData?.requires_sponsorship === true ? "needed"
    : initialData?.requires_sponsorship === false ? "none"
    : null
  );
  const [contractTypes, setContractTypes] = useState<string[]>(initialData?.contract_types ?? []);
  const [availability, setAvailability] = useState<string | null>(initialData?.availability ?? null);
  const [targetSeniority, setTargetSeniority] = useState<SeniorityId | null>(
    (initialData?.target_seniority as SeniorityId | null) ?? null
  );
  const [salaryMin, setSalaryMin] = useState(initialData?.salary?.min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = useState(initialData?.salary?.max?.toString() ?? "");
  const [currency, setCurrency] = useState(initialData?.salary?.currency ?? "EUR");
  const [salaryPeriod, setSalaryPeriod] = useState<string>(initialData?.salary?.period ?? "year");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    sponsorship !== null &&
    contractTypes.length >= 1 &&
    availability !== null &&
    !salaryError;

  const toggleGoal = useCallback((id: string) => {
    setGoalIds((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : prev.length < 3 ? [...prev, id] : prev
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
        requires_sponsorship: sponsorship === "needed",
        contract_types: contractTypes,
        availability: availability ?? undefined,
        target_seniority: targetSeniority ?? undefined,
        salary_min: salaryMin ? parseInt(salaryMin) : undefined,
        salary_max: salaryMax ? parseInt(salaryMax) : undefined,
        salary_currency: salaryMin || salaryMax ? currency : undefined,
        salary_period: salaryMin || salaryMax ? salaryPeriod : "year",
        salary_negotiable: true,
      });
      onComplete();
    } catch {
      setError("Failed to save. Please try again.");
      setSaving(false);
    }
  };

  const labelCls = "block text-[11px] font-semibold tracking-wider uppercase mb-1 text-[var(--text-muted)]";
  const stepIdx = STEP_ORDER.indexOf("GOALS" as never);

  return (
    <div className="w-full">
      {/* Top bar — same language as BUILDING split */}
      <div className="flex items-center justify-between mb-4">
        <AplioLogo variant="wordmark" size="md" />
        {stepIdx >= 0 && (
          <p className="text-[11px] font-medium tracking-widest uppercase text-[var(--text-muted)]">
            Step {stepIdx + 1} / {STEP_ORDER.length}
          </p>
        )}
      </div>
      <div className="flex items-center gap-1 mb-6">
        {STEP_ORDER.map((s, i) => (
          <div
            key={s}
            className="h-0.5 flex-1 rounded-full transition-all duration-300"
            style={{
              background: "var(--accent)",
              opacity: i < stepIdx ? 1 : i === stepIdx ? 0.6 : 0.15,
            }}
          />
        ))}
      </div>

      <div className="mb-5">
        <NarrativeText size="xl" weight="semibold">Where do you want to go?</NarrativeText>
        <p className="text-[13px] mt-0.5 text-[var(--text-muted)]">
          {roleTitle ? `Priorities tuned for ${roleTitle}. ` : ""}Pick what matters — we tune the rest.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-2 bg-[rgba(235,94,85,0.1)] border border-[rgba(235,94,85,0.2)] rounded-lg text-xs text-[var(--danger)]">
          {error}
        </div>
      )}

      {/* ── Editorial two-column ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">

        {/* LEFT — intent */}
        <div className="space-y-5">

          {/* Goals — role-aware, staggered reveal, "for you" dot */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className={labelCls + " mb-0"}>Optimizing for *</label>
              <span className="text-[10px] text-[var(--text-muted)]">{goalIds.length}/3</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {catalog.map((g, i) => {
                const sel = goalIds.includes(g.id);
                const disabled = !sel && goalIds.length >= 3;
                return (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => toggleGoal(g.id)}
                    disabled={disabled}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all duration-200 animate-fade-in"
                    style={{
                      animationDelay: `${i * 35}ms`,
                      borderColor: sel ? "var(--accent)" : "var(--border)",
                      background: sel ? "rgba(255,177,98,0.06)" : "var(--surface)",
                      color: sel ? "var(--accent)" : "var(--text-secondary)",
                      opacity: disabled ? 0.35 : 1,
                      cursor: disabled ? "not-allowed" : "pointer",
                      boxShadow: sel
                        ? "0 0 0 1px var(--accent), 0 4px 14px -6px rgba(255,177,98,0.45)"
                        : "none",
                    }}
                  >
                    {/* Pulsed "for you" dot — only shown when not selected */}
                    {g.suggested && !sel && (
                      <span className="relative flex h-1.5 w-1.5">
                        <span
                          className="absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping"
                          style={{ background: "var(--accent)" }}
                        />
                        <span
                          className="relative inline-flex h-1.5 w-1.5 rounded-full"
                          style={{ background: "var(--accent)" }}
                        />
                      </span>
                    )}
                    {sel && <Check className="h-3 w-3" strokeWidth={2.5} />}
                    {g.label}
                  </button>
                );
              })}
            </div>
            {catalog.some((g) => g.suggested) && (
              <p className="flex items-center gap-1 mt-1.5 text-[10px] text-[var(--text-muted)]">
                <Sparkles className="h-3 w-3" style={{ color: "var(--accent)" }} />
                pulsed = tuned for {roleTitle ?? "your role"}
              </p>
            )}
          </div>

          {/* Target roles */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={labelCls + " mb-0"}>Target roles *</label>
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

          {/* Target locations */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={labelCls + " mb-0"}>Target locations *</label>
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
        </div>

        {/* RIGHT — logistics */}
        <div className="space-y-4">

          {/* Work arrangement */}
          <div>
            <label className={labelCls}>Work arrangement *</label>
            <div className="grid grid-cols-3 gap-1.5">
              {WORK_ARRANGEMENTS.map(({ id, label }) => {
                const sel = workArr.includes(id);
                return (
                  <div key={id} className="group/onsite relative">
                    <button
                      type="button"
                      onClick={() =>
                        setWorkArr((p) =>
                          sel ? (p.length > 1 ? p.filter((a) => a !== id) : p) : [...p, id]
                        )
                      }
                      className="w-full py-1.5 rounded-lg border text-xs font-semibold transition-all duration-200"
                      style={{
                        borderColor: sel ? "var(--accent)" : "var(--border)",
                        background: sel ? "rgba(255,177,98,0.05)" : "var(--surface)",
                        color: sel ? "var(--accent)" : "var(--text-secondary)",
                      }}
                    >
                      {label}
                    </button>
                    {id === "onsite" && (
                      <span
                        className="pointer-events-none absolute left-1/2 -translate-x-1/2 -top-2 -translate-y-full z-20 w-max max-w-[210px] px-2.5 py-1.5 rounded-md text-[10px] leading-snug text-center opacity-0 translate-y-1 transition-all duration-200 group-hover/onsite:opacity-100 group-hover/onsite:translate-y-0"
                        style={{
                          background: "var(--surface-elevated, #1c2530)",
                          border: "1px solid var(--border-strong)",
                          color: "var(--text-secondary)",
                          boxShadow: "0 10px 28px -14px rgba(0,0,0,0.7)",
                        }}
                      >
                        Required for clinical, field, studio &amp; on-prem roles
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Contract type */}
          <div>
            <label className={labelCls}>Contract type *</label>
            <div className="flex flex-wrap gap-1.5">
              {(["full_time", "contract", "freelance", "part_time"] as const).map((c) => {
                const sel = contractTypes.includes(c);
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() =>
                      setContractTypes((p) => (sel ? p.filter((x) => x !== c) : [...p, c]))
                    }
                    className="px-3 py-1.5 rounded-full border text-xs font-medium transition-all"
                    style={{
                      borderColor: sel ? "var(--accent)" : "var(--border)",
                      background: sel ? "rgba(255,177,98,0.05)" : "var(--surface)",
                      color: sel ? "var(--accent)" : "var(--text-secondary)",
                    }}
                  >
                    {c.replace("_", "-")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Availability */}
          <div>
            <label className={labelCls}>Availability *</label>
            <div className="flex flex-wrap gap-1.5">
              {(
                [
                  ["immediately", "Immediately"],
                  ["2_weeks",     "2 weeks"],
                  ["1_month",     "1 month"],
                  ["3_months_plus", "3 months+"],
                ] as const
              ).map(([v, l]) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setAvailability(v)}
                  className="px-3 py-1.5 rounded-full border text-xs font-medium transition-all"
                  style={{
                    borderColor: availability === v ? "var(--accent)" : "var(--border)",
                    background: availability === v ? "rgba(255,177,98,0.05)" : "var(--surface)",
                    color: availability === v ? "var(--accent)" : "var(--text-secondary)",
                  }}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>

          {/* Target seniority — neutral ladder with weight dots */}
          <div>
            <label className={labelCls}>Target seniority</label>
            <div className="flex gap-1.5">
              {SENIORITY.map((lv) => {
                const active = targetSeniority === lv.id;
                return (
                  <button
                    key={lv.id}
                    type="button"
                    onClick={() => setTargetSeniority(lv.id)}
                    className="flex-1 py-1.5 rounded-lg border text-[11px] font-semibold transition-all duration-200"
                    style={{
                      borderColor: active ? "var(--accent)" : "var(--border)",
                      background: active ? "rgba(255,177,98,0.05)" : "var(--surface)",
                      color: active ? "var(--accent)" : "var(--text-secondary)",
                      boxShadow: active
                        ? "0 0 0 1px var(--accent), 0 4px 14px -6px rgba(255,177,98,0.5)"
                        : "none",
                    }}
                  >
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

          {/* Visa sponsorship */}
          <div>
            <label className={labelCls}>Visa sponsorship *</label>
            <div className="grid grid-cols-2 gap-1.5">
              {(
                [
                  { val: "none",   icon: ShieldCheck, label: "No sponsorship", desc: "Work permit ready" },
                  { val: "needed", icon: Stamp,        label: "Need sponsorship", desc: "Require visa support" },
                ] as const
              ).map(({ val, icon: Icon, label, desc }) => {
                const sel = sponsorship === val;
                return (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setSponsorship(val)}
                    className="flex items-center gap-2 p-2 rounded-lg border text-left transition-all"
                    style={{
                      borderColor: sel ? "var(--accent)" : "var(--border)",
                      background: sel ? "rgba(255,177,98,0.05)" : "var(--surface)",
                    }}
                  >
                    <Icon
                      className="h-3.5 w-3.5 shrink-0"
                      style={{ color: sel ? "var(--accent)" : "var(--text-muted)" }}
                    />
                    <div>
                      <div className="text-xs font-semibold text-[var(--text-primary)]">{label}</div>
                      <div className="text-[10px] leading-snug text-[var(--text-muted)]">{desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Salary — the unit set morphs with the contract type */}
          <div>
            <div className="flex items-baseline justify-between mb-1">
              <label className={labelCls + " mb-0"}>
                {contractTypes.some((c) => c === "freelance" || c === "contract")
                  ? "Rate expectation"
                  : "Salary expectation"}
              </label>
              <span className="text-[10px] italic text-[var(--text-muted)]">optional</span>
            </div>

            {(() => {
              const isRate = contractTypes.some((c) => c === "freelance" || c === "contract");
              const units = isRate
                ? ([["hour", "/ hr"], ["day", "/ day"], ["project", "/ project"]] as const)
                : ([["year", "/ yr"], ["month", "/ mo"]] as const);
              const effective = units.some((u) => u[0] === salaryPeriod) ? salaryPeriod : units[0][0];
              if (effective !== salaryPeriod) queueMicrotask(() => setSalaryPeriod(effective));
              const unitLabel = units.find((u) => u[0] === effective)?.[1] ?? "";
              return (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <select value={currency} onChange={(e) => setCurrency(e.target.value)}
                      className="w-20 px-2 py-1.5 rounded-lg border text-xs outline-none"
                      style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}>
                      {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                    <input type="number" value={salaryMin} onChange={(e) => setSalaryMin(e.target.value)}
                      placeholder={`Min ${unitLabel}`}
                      className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
                      style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
                      onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                      onBlur={(e) => (e.target.style.borderColor = "var(--border)")} />
                    <span className="text-[var(--text-muted)] text-sm">—</span>
                    <input type="number" value={salaryMax} onChange={(e) => setSalaryMax(e.target.value)}
                      placeholder={`Max ${unitLabel}`}
                      className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
                      style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
                      onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                      onBlur={(e) => (e.target.style.borderColor = "var(--border)")} />
                  </div>
                  <div key={isRate ? "rate" : "salary"} className="flex gap-1.5 animate-fade-in">
                    {units.map(([v, l]) => (
                      <button key={v} type="button" onClick={() => setSalaryPeriod(v)}
                        className="px-2.5 py-1 rounded-md border text-[10px] font-semibold transition-all"
                        style={{
                          borderColor: effective === v ? "var(--accent)" : "var(--border)",
                          background: effective === v ? "rgba(255,177,98,0.06)" : "var(--surface)",
                          color: effective === v ? "var(--accent)" : "var(--text-muted)",
                        }}>{l}</button>
                    ))}
                  </div>
                </div>
              );
            })()}
            {salaryError && <p className="text-[10px] text-[var(--danger)] mt-1">{salaryError}</p>}
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={saving || !isValid}
        className="w-full mt-6 py-2.5 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
        style={{
          background: !isValid || saving ? "var(--surface-hover)" : "var(--accent)",
          color: !isValid || saving ? "var(--text-muted)" : "var(--accent-fg)",
          cursor: !isValid || saving ? "not-allowed" : "pointer",
        }}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}
