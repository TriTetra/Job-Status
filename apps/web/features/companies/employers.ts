import { apiFetch } from "@/lib/api/client";

export interface Employer {
  name: string;
  domain: string | null;
  sector: string;
  city: string | null;
  careers_url: string;
  ats: string | null;
  board_key: string | null;
  note: string | null;
  tracked: boolean;
  open_roles: number;
}

export interface EmployersDirectory {
  country: string;
  count: number;
  tracked: number;
  sectors: { id: string; label: string }[];
  employers: Employer[];
}

export const fetchEmployers = (country = "tr") =>
  apiFetch<EmployersDirectory>(`/api/companies/employers?country=${encodeURIComponent(country)}`);
