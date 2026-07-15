/**
 * Roles API client — search and retrieve canonical tech roles.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  async getAll(): Promise<Role[]> {
    const response = await fetch(`${API_BASE}/api/roles`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error("Failed to fetch roles");
    return response.json();
  },

  async search(query: string, limit = 10): Promise<RoleSearchResult[]> {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    const response = await fetch(`${API_BASE}/api/roles/search?${params}`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error("Failed to search roles");
    return response.json();
  },

  async getCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/api/roles/categories`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error("Failed to fetch categories");
    return response.json();
  },

  async getBySlug(slug: string): Promise<Role> {
    const response = await fetch(`${API_BASE}/api/roles/${slug}`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error(`Role '${slug}' not found`);
    return response.json();
  },
};
