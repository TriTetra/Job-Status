import { apiFetch } from "@/lib/api/client";
import type { GithubStatus, PortfolioStatus } from "@/features/onboarding/types";
export { API_BASE } from "@/lib/api/client";
/**
 * Settings API client — onboarding ile AYNI tabloları konuşur.
 * users / career_preferences / user_settings / connected_accounts.
 */

export interface ScoringWeights {
  fit: number;
  acceptance: number;
  career_value: number;
  market_demand: number;
}

/** GET/PATCH /api/preferences (apps/api/app/routers/preferences.py: PreferencesOut). */
export interface Preferences {
  goal_ids: string[];
  preferred_role_ids: string[];
  preferred_country_codes: string[];
  work_arrangements: string[];
  requires_sponsorship: boolean | null;
  salary: { min: number | null; max: number | null; currency: string | null; period: string; negotiable: boolean } | null;
  pref_metadata: { communication_style?: string; [key: string]: unknown };
  created_at: string | null;
  updated_at: string | null;
}

export const settingsApi = {
  // ── Profile (users tablosu — onboarding ile aynı) ─────────────────────
  saveIdentity: (data: Record<string, unknown>) =>
    apiFetch<{ state: string; message: string }>("/api/onboarding/identity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // ── Preferences (career_preferences tablosu) ──────────────────────────
  getPreferences: () => apiFetch<Preferences>("/api/preferences"),

  patchPreferences: (data: Record<string, unknown>) =>
    apiFetch<Preferences>("/api/preferences", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // ── Scoring weights (user_settings tablosu) ───────────────────────────
  getWeights: () =>
    apiFetch<{ user_id: string; weights: ScoringWeights }>("/api/settings/weights"),

  saveWeights: (weights: ScoringWeights) =>
    apiFetch<{ user_id: string; weights: ScoringWeights }>("/api/settings/weights", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weights }),
    }),

  // ── Connections ────────────────────────────────────────────────────────
  getGithubStatus: () => apiFetch<GithubStatus>("/api/oauth/github/status"),
  getPortfolioStatus: () => apiFetch<PortfolioStatus>("/api/evidence/portfolio/status"),
  disconnectGithub: () => apiFetch<{ status: string }>("/api/oauth/github", { method: "DELETE" }),
  disconnectPortfolio: () => apiFetch<{ status: string }>("/api/evidence/portfolio", { method: "DELETE" }),
  crawlPortfolio: (url: string) =>
    apiFetch<{ status: string; projects_found: number; technologies_found: number; evidence_created: number }>("/api/evidence/portfolio/crawl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
};
