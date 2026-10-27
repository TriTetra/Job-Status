"use client";

import { useMemo, useState, useCallback } from "react";
import { SearchableCombobox, type ComboboxOption } from "@/components/shared/searchable-combobox";
import { rolesApi } from "@/features/onboarding/api/roles";
import { ROLES } from "@/features/onboarding/data/roles";
import { COUNTRIES, SENIORITY, type SeniorityId } from "@/features/onboarding";
import { settingsApi } from "@/features/settings/api";
import { Section, Row, UnderlineInput, SaveBar } from "./kit";
import type { InitialProfile } from "./settings-shell";

export function ProfileTab({ initial }: { initial: InitialProfile | null }) {
  const pd = initial?.profileData ?? {};

  const [firstName,   setFirstName]   = useState<string>(pd.first_name ?? "");
  const [lastName,    setLastName]    = useState<string>(pd.last_name ?? "");
  const [country,     setCountry]     = useState<string>(pd.country ?? "");
  const [roleId,      setRoleId]      = useState<string>(initial?.currentRoleId ?? "");
  const [roleTitle,   setRoleTitle]   = useState<string>(pd.current_role_title ?? "");
  const [yearsInRole, setYearsInRole] = useState<number>(initial?.yearsInRole ?? 0);
  const [level,       setLevel]       = useState<SeniorityId>((initial?.careerLevel as SeniorityId) ?? "mid");

  const [saving, setSaving] = useState(false);
  const [saved,  setSaved]  = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  const staticRoles: ComboboxOption[] = useMemo(
    () => ROLES.map((r) => ({ id: r.id, title: r.title, category: r.category, aliases: r.aliases })),
    []
  );
  const countryOptions: ComboboxOption[] = useMemo(
    () => COUNTRIES.map((c) => ({ id: c.name, title: c.name, category: c.region })),
    []
  );

  const handleRoleSearch = useCallback(async (query: string): Promise<ComboboxOption[]> => {
    const results = await rolesApi.search(query, 12);
    return results.map((r) => ({ id: r.id, title: r.title, category: r.category, aliases: r.aliases }));
  }, []);

  const isValid = firstName.trim().length > 0 && roleId.length > 0 && country.length > 0;

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await settingsApi.saveIdentity({
        first_name: firstName,
        last_name: lastName || undefined,
        current_role_id: roleId,
        current_role_title: roleTitle,
        years_in_role: yearsInRole,
        career_level: level,
        career_level_origin: "user",
        country,
        total_years: pd.total_years,
        languages: pd.languages ?? [],
        education_level: pd.education_level,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Section title="Identity">
        <Row label="Full name" hint="Shown on your briefing and resumes">
          <div className="flex items-center gap-3">
            <UnderlineInput
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="First name"
            />
            <UnderlineInput
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Last name"
            />
          </div>
        </Row>
        <Row label="Email" hint="Managed by your account provider">
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>
            {initial?.email || "—"}
          </span>
        </Row>
        <Row label="Country of residence">
          <div className="md:max-w-[260px]">
            <SearchableCombobox
              initialOptions={countryOptions}
              value={country}
              onChange={(_id, title) => setCountry(title)}
              placeholder="Search countries..."
              allowCustom={false}
              emptyMessage="No country found"
            />
          </div>
        </Row>
      </Section>

      <Section title="Experience">
        <Row label="Current role" hint="Drives role-aware suggestions">
          <div className="md:max-w-[320px]">
            <SearchableCombobox
              initialOptions={staticRoles}
              onSearch={handleRoleSearch}
              value={roleId}
              valueLabel={roleTitle}
              onChange={(id, title) => {
                setRoleId(id);
                setRoleTitle(title);
              }}
              placeholder="Search roles..."
              allowCustom={true}
              customLabel='Use "{query}" as my role'
            />
          </div>
        </Row>
        <Row label="Years in this role">
          <UnderlineInput
            type="number"
            min={0}
            max={50}
            value={yearsInRole}
            onChange={(e) => setYearsInRole(Number(e.target.value) || 0)}
            className="md:max-w-[80px]"
          />
        </Row>
        <Row label="Career level">
          <div className="flex gap-1.5">
            {SENIORITY.map((lv) => (
              <button
                key={lv.id}
                type="button"
                onClick={() => setLevel(lv.id)}
                className="flex-1 md:flex-none md:px-3 py-1.5 rounded-lg border text-[11px] font-semibold transition-all cursor-pointer"
                style={{
                  borderColor: level === lv.id ? "var(--accent)" : "var(--border)",
                  background:  level === lv.id ? "rgba(255,177,98,0.05)" : "transparent",
                  color:       level === lv.id ? "var(--accent)" : "var(--text-secondary)",
                }}
              >
                {lv.label}
              </button>
            ))}
          </div>
        </Row>
      </Section>

      {error && (
        <p className="text-xs mt-4" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      <SaveBar onSave={handleSave} saving={saving} saved={saved} disabled={!isValid} />
    </div>
  );
}
