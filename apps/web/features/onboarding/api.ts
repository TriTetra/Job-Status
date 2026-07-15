import type { OnboardingStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${path}: ${res.status} ${text}`);
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
    authorization: string;
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

  async uploadResume(file: File): Promise<{ job_id: string; status: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/onboarding/resume`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to upload resume");
    }

    return response.json();
  },

  async getResumeStatus(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/api/onboarding/resume/${jobId}/status`, {
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to get status");
    }

    return response.json();
  },

  async buildGraph(): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE}/api/onboarding/build-graph`, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to start graph building");
    }

    return response.json();
  },

  async getGraphStatus(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/api/onboarding/build-graph/${jobId}/status`, {
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to get graph status");
    }

    return response.json();
  },
};
