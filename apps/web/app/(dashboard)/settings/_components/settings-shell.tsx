"use client";

import { useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { ProfileTab } from "./profile-tab";
import { PreferencesTab } from "./preferences-tab";
import { ScoringTab } from "./scoring-tab";
import { AccountTab } from "./account-tab";

/** users.profile_data as written by the identity step. */
export interface ProfileData {
  first_name?: string;
  last_name?: string | null;
  country?: string;
  current_role_title?: string;
  total_years?: number | null;
  languages?: Array<{ code: string; level: string }>;
  education_level?: string | null;
  [key: string]: unknown;
}

export interface InitialProfile {
  profileData: ProfileData;
  yearsInRole: number;
  careerLevel: string;
  currentRoleId: string;
  email: string;
}

const NAV = [
  ["profile", "Profile"],
  ["preferences", "Preferences"],
  ["scoring", "Scoring"],
  ["account", "Account"],
] as const;

type TabId = (typeof NAV)[number][0];

export function SettingsShell({ initialProfile }: { initialProfile: InitialProfile | null }) {
  const [tab, setTab] = useState<TabId>("profile");

  return (
    <div className="narrative-container px-6 lg:px-8 py-14">
      <NarrativeText size="2xl" weight="semibold" as="h1">Settings</NarrativeText>
      <p className="text-sm mt-1 mb-10" style={{ color: "var(--text-secondary)" }}>
        Your profile, your preferences, and how Aplio scores for you.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-10">
        {/* Left nav — plain list, hairline accent on active */}
        <nav className="md:sticky md:top-24 h-fit space-y-1">
          {NAV.map(([id, label]) => {
            const active = tab === id;
            return (
              <button
                key={id}
                onClick={() => setTab(id)}
                className="relative w-full text-left text-sm py-1.5 transition-colors cursor-pointer"
                style={{
                  color: active ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: active ? 500 : 400,
                }}
              >
                {active && (
                  <span
                    className="absolute -left-4 top-1/2 -translate-y-1/2 h-4 w-[2px]"
                    style={{ background: "var(--accent)" }}
                  />
                )}
                {label}
              </button>
            );
          })}
        </nav>

        {/* Content */}
        <div>
          {tab === "profile"     && <ProfileTab initial={initialProfile} />}
          {tab === "preferences" && <PreferencesTab />}
          {tab === "scoring"     && <ScoringTab />}
          {tab === "account"     && <AccountTab />}
        </div>
      </div>
    </div>
  );
}
