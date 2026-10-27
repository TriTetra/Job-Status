/**
 * Roles API client — search and retrieve canonical tech roles.
 */

import { apiFetch } from "@/lib/api/client";

export interface Role {
  id: string;
  slug: string;
  title: string;
  category: string;
  aliases: string[];
  metadata: {
    family?: string;
    track?: string;
    specialization?: string;
    skills?: string[];
    adjacent_roles?: string[];
    next_roles?: string[];
    seniority_range?: string[];
  };
}

export interface RoleSearchResult extends Role {
  score: number;
}

export const rolesApi = {
  getAll: () => apiFetch<Role[]>("/api/roles"),

  search: (query: string, limit = 10) =>
    apiFetch<RoleSearchResult[]>(`/api/roles/search?${new URLSearchParams({ q: query, limit: String(limit) })}`),

  getCategories: () => apiFetch<string[]>("/api/roles/categories"),

  getBySlug: (slug: string) => apiFetch<Role>(`/api/roles/${encodeURIComponent(slug)}`),
};
