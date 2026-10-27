import { apiFetch } from "@/lib/api/client";

import type { Company } from "./types";

export const companiesApi = {
  list: () => apiFetch<Company[]>("/api/companies/"),
  track: (name: string) =>
    apiFetch<Company>(`/api/companies/track?name=${encodeURIComponent(name)}`, { method: "POST" }),
};
