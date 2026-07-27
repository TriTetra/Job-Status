import type { OnboardingStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  // Her istekte TAZE token al — SDK expired ise otomatik refresh eder
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

export const onboardingApi = {
  getState(): Promise<OnboardingStatus> {
    return apiFetch("/api/onboarding/state");
  },

  saveIdentity(data: {
    first_name: string;
    last_name?: string;
    current_role_id: string;
    current_role_title: string;
    years_in_role: number;
    career_level?: string;
    career_level_origin?: string;
    country: string;
    total_years?: number;
    languages?: Array<{ code: string; level: string }>;
    education_level?: string;
  }): Promise<{ state: string; message: string }> {
    return apiFetch("/api/onboarding/identity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  saveGoals(data: {
    goal_ids: string[];
    preferred_role_ids: string[];
    preferred_country_codes: string[];
    work_arrangements: string[];
    requires_sponsorship?: boolean;   // ← YENİ
    contract_types?: string[];
    availability?: string;
    target_seniority?: string;
    salary_min?: number;
    salary_max?: number;
    salary_currency?: string;
    salary_period?: string;
    salary_negotiable?: boolean;
  }): Promise<{ state: string; message: string }> {
    return apiFetch("/api/onboarding/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  advance(): Promise<{ state: string }> {
    return apiFetch("/api/onboarding/advance", { method: "POST" });
  },

  complete(): Promise<{ state: string; message: string }> {
    return apiFetch("/api/onboarding/complete", { method: "POST" });
  },

  // FormData → Content-Type KOYMA (boundary otomatik)
  uploadResume(file: File): Promise<{ job_id: string; status: string }> {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch("/api/onboarding/resume", { method: "POST", body: formData });
  },

  getResumeStatus(jobId: string): Promise<any> {
    return apiFetch(`/api/onboarding/resume/${jobId}/status`);
  },

  buildGraph(): Promise<{ job_id: string; status: string }> {
    return apiFetch("/api/onboarding/build-graph", { method: "POST" });
  },

  getGraphStatus(jobId: string): Promise<any> {
    return apiFetch(`/api/onboarding/build-graph/${jobId}/status`);
  },

  getEvidenceItems(source?: string): Promise<{
    skills: Array<{
      id: string;
      name: string;
      skill_id: number | null;
      confidence: number;
      source: string;
      evidence_text: string | null;
      evidence_data: Record<string, any>;
    }>;
    projects: Array<any>;
    experiences: Array<any>;
    education: Array<any>;
    certifications: Array<any>;
  }> {
    const params = source ? `?source=${source}` : '';
    return apiFetch(`/api/evidence/items${params}`);
  },

  async deleteEvidenceItem(itemId: string): Promise<void> {
    await apiFetch(`/api/evidence/items/${itemId}`, {
      method: 'DELETE',
    });
  },

  getCareerGraph(): Promise<any> {
    return apiFetch("/api/onboarding/career-graph");
  },

  getGithubStatus(): Promise<{
    connected: boolean;
    username?: string;
    provider_user_id?: string;
    metadata?: any;
    last_synced_at?: string | null;
  }> {
    return apiFetch("/api/oauth/github/status");
  },

  syncGithub(): Promise<{
    status: string;
    repos_analyzed: number;
    skills_created: number;
    projects_created: number;
  }> {
    return apiFetch("/api/oauth/github/sync", {
      method: 'POST',
    });
  },

  async disconnectGithub(): Promise<void> {
    await apiFetch("/api/oauth/github", {
      method: 'DELETE',
    });
  },

  getAggregatedSkills(): Promise<{
    skills: Array<{
      skill_name: string;
      canonical_id: string | null;
      aggregated_confidence: number;
      sources: Array<{
        type: string;
        confidence: number;
        count: number;
      }>;
      total_evidence_count: number;
    }>;
  }> {
    return apiFetch("/api/evidence/skills/aggregated");
  },

  crawlPortfolio(url: string): Promise<{
    status: string;
    projects_found: number;
    technologies_found: number;
    evidence_created: number;
  }> {
    return apiFetch("/api/evidence/portfolio/crawl", {
      method: 'POST',
      body: JSON.stringify({ url }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  getPortfolioStatus(): Promise<{
    connected: boolean;
    url?: string;
    last_synced_at?: string | null;
  }> {
    return apiFetch("/api/evidence/portfolio/status");
  },

  async disconnectPortfolio(): Promise<void> {
    await apiFetch("/api/evidence/portfolio", {
      method: 'DELETE',
    });
  },

  getEvidenceSources(): Promise<{
    recommended: Array<{
      id: string; label: string; icon: string; category: string;
      status: string; connect_kind: string; oauth_provider: string | null;
      connected: boolean; suggested: boolean;
    }>;
    all: Array<{
      id: string; label: string; icon: string; category: string;
      status: string; connect_kind: string; oauth_provider: string | null;
      connected: boolean; suggested: boolean;
    }>;
    connected: Record<string, boolean>;
    role_title: string | null;
  }> {
    return apiFetch("/api/evidence/sources");
  },

  getGoalCatalog(): Promise<{
    goals: Array<{ id: string; label: string; theme: string; suggested: boolean }>;
    role_title: string | null;
    role_category: string | null;
  }> {
    return apiFetch("/api/goals/catalog");
  },
};

