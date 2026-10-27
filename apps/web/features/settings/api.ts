/**
 * Settings API client — onboarding ile AYNI tabloları konuşur.
 * users / career_preferences / user_settings / connected_accounts.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  if (typeof window !== "undefined") {
    const clerk = (window as any).Clerk;
    const token = await clerk?.session?.getToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...init,
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${path}: ${res.status} ${text}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export interface ScoringWeights {
  fit: number;
  acceptance: number;
  career_value: number;
  market_demand: number;
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
  getPreferences: () => apiFetch<Record<string, any>>("/api/preferences"),

  patchPreferences: (data: Record<string, unknown>) =>
    apiFetch<Record<string, any>>("/api/preferences", {
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
  getGithubStatus: () => apiFetch<Record<string, any>>("/api/oauth/github/status"),
  getPortfolioStatus: () => apiFetch<Record<string, any>>("/api/evidence/portfolio/status"),
  disconnectGithub: () => apiFetch<any>("/api/oauth/github", { method: "DELETE" }),
  disconnectPortfolio: () => apiFetch<any>("/api/evidence/portfolio", { method: "DELETE" }),
  crawlPortfolio: (url: string) =>
    apiFetch<any>("/api/evidence/portfolio/crawl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
};
