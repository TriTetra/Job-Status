import { apiFetch } from "@/lib/api/client";
import type { Opportunity } from "@/features/opportunities/types";

/** A search hit: an opportunity, scored by the scan (in_opportunities) or just now for this search. */
export type SearchResult = Opportunity & { in_opportunities: boolean };

export interface SearchResponse {
  total: number;
  capped: boolean;
  country?: string | null;  // the country searched, also when typed in the box ("İstanbul")
  jobs: SearchResult[];
}

export type Work = "remote" | "hybrid" | "onsite";
export type Size = "startup" | "midsize" | "large";

export interface SearchQuery {
  q: string;
  country: string;
  work: Work[];
  size: Size[];
  reliable: boolean;
  reachable: boolean;
  visa: boolean;
  minSalary: number | null;
  source: "" | "company" | "feed";
  days: number | null;
  sort: "score" | "newest";
}

export const EMPTY_QUERY: SearchQuery = {
  q: "", country: "", work: [], size: [], reliable: false, reachable: true, visa: false,
  minSalary: null, source: "", days: null, sort: "score",
};

const WORKS: Work[] = ["remote", "hybrid", "onsite"];
const SIZES: Size[] = ["startup", "midsize", "large"];

const list = <T extends string>(v: string | null, allowed: T[]) =>
  (v ?? "").split(",").filter((x): x is T => (allowed as string[]).includes(x));
const num = (v: string | null) => (v && /^\d+$/.test(v) ? Number(v) : null);

/** The page URL ↔ the query, so a search can be shared, bookmarked and survives reload. */
export function fromParams(p: URLSearchParams): SearchQuery {
  const source = p.get("source");
  return {
    q: (p.get("q") ?? "").slice(0, 120),
    country: /^[A-Z]{2}$/.test(p.get("country") ?? "") ? p.get("country")! : "",
    work: list(p.get("work"), WORKS),
    size: list(p.get("size"), SIZES),
    reliable: p.get("reliable") === "1",
    reachable: p.get("reachable") !== "0",
    visa: p.get("visa") === "1",
    minSalary: num(p.get("pay")),
    source: source === "company" || source === "feed" ? source : "",
    days: num(p.get("days")),
    sort: p.get("sort") === "newest" ? "newest" : "score",
  };
}

/** Only what differs from the defaults (the page URL). */
export function toParams(s: SearchQuery): URLSearchParams {
  const p = new URLSearchParams();
  if (s.q.trim()) p.set("q", s.q.trim());
  if (s.country) p.set("country", s.country);
  if (s.work.length) p.set("work", s.work.join(","));
  if (s.size.length) p.set("size", s.size.join(","));
  if (s.reliable) p.set("reliable", "1");
  if (!s.reachable) p.set("reachable", "0");
  if (s.visa) p.set("visa", "1");
  if (s.minSalary) p.set("pay", String(s.minSalary));
  if (s.source) p.set("source", s.source);
  if (s.days) p.set("days", String(s.days));
  if (s.sort !== "score") p.set("sort", s.sort);
  return p;
}

/** The API's parameter names. */
function apiParams(s: SearchQuery, offset: number, limit: number): URLSearchParams {
  const p = new URLSearchParams({ sort: s.sort, offset: String(offset), limit: String(limit) });
  if (s.q.trim()) p.set("q", s.q.trim());
  if (s.country) p.set("country", s.country);
  if (s.work.length) p.set("work", s.work.join(","));
  if (s.size.length) p.set("size", s.size.join(","));
  p.set("reliable", String(s.reliable));
  p.set("reachable", String(s.reachable));
  p.set("visa", String(s.visa));
  if (s.minSalary) p.set("min_salary", String(s.minSalary));
  if (s.source) p.set("source", s.source);
  if (s.days) p.set("days", String(s.days));
  return p;
}

export const PAGE = 50;

export const searchApi = {
  run: (s: SearchQuery, offset = 0, limit = PAGE) =>
    apiFetch<SearchResponse>(`/api/jobs/search?${apiParams(s, offset, limit)}`),
};

/** Countries people search most here first, then the rest A–Z (codes as in careeros/jobs/geo.py). */
export const COUNTRIES: { code: string; name: string }[] = [
  { code: "TR", name: "Türkiye" }, { code: "DE", name: "Germany" }, { code: "GB", name: "United Kingdom" },
  { code: "CH", name: "Switzerland" }, { code: "ES", name: "Spain" }, { code: "NL", name: "Netherlands" },
  { code: "IE", name: "Ireland" }, { code: "FR", name: "France" }, { code: "PL", name: "Poland" },
  { code: "PT", name: "Portugal" }, { code: "AT", name: "Austria" }, { code: "SE", name: "Sweden" },
  { code: "DK", name: "Denmark" }, { code: "FI", name: "Finland" }, { code: "NO", name: "Norway" },
  { code: "IT", name: "Italy" }, { code: "BE", name: "Belgium" }, { code: "CZ", name: "Czechia" },
  { code: "EE", name: "Estonia" }, { code: "LT", name: "Lithuania" }, { code: "RO", name: "Romania" },
  { code: "GR", name: "Greece" }, { code: "LU", name: "Luxembourg" }, { code: "AE", name: "United Arab Emirates" },
  { code: "SA", name: "Saudi Arabia" }, { code: "IL", name: "Israel" }, { code: "US", name: "United States" },
  { code: "CA", name: "Canada" }, { code: "SG", name: "Singapore" }, { code: "JP", name: "Japan" },
  { code: "AU", name: "Australia" }, { code: "IN", name: "India" }, { code: "BR", name: "Brazil" },
];
