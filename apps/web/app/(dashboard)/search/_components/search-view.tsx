"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Loader2, Search } from "lucide-react";
import { OpportunityCardCompact } from "@/components/ui/opportunity-card-compact";
import { OpportunityDetailPanel } from "@/components/ui/opportunity-detail-panel";
import { opportunitiesApi } from "@/features/opportunities/api";
import {
  COUNTRIES, EMPTY_QUERY, PAGE, fromParams, searchApi, toParams,
  type SearchQuery, type SearchResponse, type SearchResult, type Size, type Work,
} from "@/features/search/api";

const WORK: { id: Work; label: string }[] = [
  { id: "remote", label: "Remote" }, { id: "hybrid", label: "Hybrid" }, { id: "onsite", label: "On-site" },
];
const SIZE: { id: Size; label: string }[] = [
  { id: "startup", label: "Startup" }, { id: "midsize", label: "Mid-size" }, { id: "large", label: "Large" },
];
const DAYS = [{ v: 1, label: "Last 24 hours" }, { v: 3, label: "Last 3 days" }, { v: 7, label: "Last week" }, { v: 30, label: "Last month" }];
const PAY = [40_000, 60_000, 80_000, 100_000, 150_000];
const LABEL = "text-[11px] uppercase tracking-[0.08em] shrink-0";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

type Results = { key: string; data: SearchResponse | null; error: boolean };

function toggle<T>(list: T[], v: T): T[] {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
}

/** Text toggles in a row: the active ones read bold with an accent underline. */
function Toggles<T extends string>({ items, value, onChange, label }: {
  items: { id: T; label: string }[]; value: T[]; onChange: (v: T[]) => void; label: string;
}) {
  return (
    <div className="flex items-center gap-3" role="group" aria-label={label}>
      <span className={LABEL} style={LABEL_STYLE}>{label}</span>
      {items.map((it) => {
        const on = value.includes(it.id);
        return (
          <button key={it.id} type="button" aria-pressed={on} onClick={() => onChange(toggle(value, it.id))}
                  className="text-sm py-0.5 border-b-2 transition-colors"
                  style={{ color: on ? "var(--text-primary)" : "var(--text-muted)", fontWeight: on ? 600 : 400,
                           borderColor: on ? "var(--accent)" : "transparent" }}>
            {it.label}
          </button>
        );
      })}
    </div>
  );
}

function Select({ label, value, onChange, children }: {
  label: string; value: string; onChange: (v: string) => void; children: React.ReactNode;
}) {
  return (
    <label className="flex items-center gap-3">
      <span className={LABEL} style={LABEL_STYLE}>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}
              className="bg-transparent border-0 border-b outline-none py-0.5 text-sm cursor-pointer focus:border-[var(--accent)] max-w-[12rem]"
              style={{ borderColor: "var(--border)", color: value ? "var(--text-primary)" : "var(--text-secondary)" }}>
        {children}
      </select>
    </label>
  );
}

const optionStyle = { background: "var(--background)", color: "var(--text-primary)" } as const;

function Check({ checked, onChange, children, title }: {
  checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode; title?: string;
}) {
  return (
    <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-muted)" }} title={title}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="accent-[var(--accent)]" />
      {children}
    </label>
  );
}

/**
 * Search: every open role Aplio reads (company job systems and feeds), not only your matches.
 * Results are scored for you as you search; nothing here changes Opportunities.
 */
export function SearchView() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const query = useMemo(() => fromParams(new URLSearchParams(params.toString())), [params]);
  const key = toParams(query).toString();

  const [draft, setDraft] = useState(query.q);
  const [results, setResults] = useState<Results>({ key: "\u0000", data: null, error: false });
  const [more, setMore] = useState(false);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  const set = useCallback((next: Partial<SearchQuery>) => {
    const qs = toParams({ ...query, ...next }).toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    setSelectedUrl(null);
  }, [query, router, pathname]);

  // Typing searches after a short pause
  useEffect(() => {
    if (draft.trim() === query.q.trim()) return;
    const t = setTimeout(() => set({ q: draft }), 350);
    return () => clearTimeout(t);
  }, [draft, query.q, set]);

  // Each query is fetched once; a late answer to an older one is dropped
  useEffect(() => {
    let live = true;
    searchApi.run(query)
      .then((data) => live && setResults({ key, data, error: false }))
      .catch(() => live && setResults({ key, data: null, error: true }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` is the query
  }, [key]);

  const loading = results.key !== key;
  const data = results.data;
  const jobs = useMemo(() => data?.jobs ?? [], [data]);
  const selected = jobs.find((j) => j.url === selectedUrl) ?? jobs[0] ?? null;

  const loadMore = async () => {
    if (!data) return;
    setMore(true);
    try {
      const next = await searchApi.run(query, data.jobs.length, PAGE);
      setResults((r) => (r.key === key && r.data
        ? { ...r, data: { ...next, jobs: [...r.data.jobs, ...next.jobs.filter((j) => !r.data!.jobs.some((x) => x.url === j.url))] } }
        : r));
    } finally {
      setMore(false);
    }
  };

  const handleDecision = async (url: string, status: "to_apply" | "applied" | "skipped") => {
    setDecisionError(null);
    setBusy(true);
    try {
      const d = await opportunitiesApi.decide(url, status);
      setResults((r) => (r.data
        ? { ...r, data: { ...r.data, jobs: r.data.jobs.map((j) => (j.url === url ? { ...j, user_decision: d } : j)) } }
        : r));
    } catch {
      setDecisionError("That didn't save. Try again.");
    } finally {
      setBusy(false);
    }
  };

  // ↑ / ↓ move through the results
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT") return;
      e.preventDefault();
      const i = jobs.findIndex((j) => j.url === selected?.url);
      const next = jobs[e.key === "ArrowUp" ? i - 1 : i + 1];
      if (next) setSelectedUrl(next.url);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [jobs, selected]);

  const isDefault = key === toParams(EMPTY_QUERY).toString();
  const countryName = COUNTRIES.find((c) => c.code === query.country)?.name;

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5">
      <header className="shrink-0 max-w-[860px]">
        <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Search</h1>
        <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Every open role Aplio reads, beyond your matches. Each result is scored for you as you search; nothing here
          changes your <Link href="/inbox" style={{ color: "var(--accent)" }}>Opportunities</Link>.
        </p>
      </header>

      {/* The query: one large line */}
      <label className="mt-5 shrink-0 flex items-center gap-3 border-b pb-2 focus-within:border-[var(--accent)] transition-colors"
             style={{ borderColor: "var(--border-strong)" }}>
        <Search className="h-5 w-5 shrink-0" style={{ color: "var(--text-muted)" }} />
        <input value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={120} autoFocus
               placeholder="Role or company, e.g. machine learning engineer"
               aria-label="Search roles or companies"
               className="flex-1 min-w-0 bg-transparent outline-none font-serif-display text-[24px] leading-tight placeholder:text-[var(--text-muted)]"
               style={{ color: "var(--text-primary)" }} />
        {(loading || more) && <Loader2 className="h-4 w-4 animate-spin shrink-0" style={{ color: "var(--text-muted)" }} aria-label="Searching" />}
      </label>

      {/* Filters */}
      <div className="mt-4 shrink-0 flex flex-wrap items-center gap-x-7 gap-y-3">
        <Select label="Where" value={query.country} onChange={(v) => set({ country: v })}>
          <option value="" style={optionStyle}>Anywhere</option>
          {COUNTRIES.map((c) => <option key={c.code} value={c.code} style={optionStyle}>{c.name}</option>)}
        </Select>
        <Toggles label="Work" items={WORK} value={query.work} onChange={(v) => set({ work: v })} />
        <Toggles label="Company" items={SIZE} value={query.size} onChange={(v) => set({ size: v })} />
        <Select label="Posted" value={query.days ? String(query.days) : ""} onChange={(v) => set({ days: v ? Number(v) : null })}>
          <option value="" style={optionStyle}>Any time</option>
          {DAYS.map((d) => <option key={d.v} value={d.v} style={optionStyle}>{d.label}</option>)}
        </Select>
        <Select label="Pay from" value={query.minSalary ? String(query.minSalary) : ""}
                onChange={(v) => set({ minSalary: v ? Number(v) : null })}>
          <option value="" style={optionStyle}>Any</option>
          {PAY.map((p) => <option key={p} value={p} style={optionStyle}>${p / 1000}k a year</option>)}
        </Select>
        <Select label="From" value={query.source} onChange={(v) => set({ source: v as SearchQuery["source"] })}>
          <option value="" style={optionStyle}>All sources</option>
          <option value="company" style={optionStyle}>Company job sites</option>
          <option value="feed" style={optionStyle}>Job feeds</option>
        </Select>
      </div>
      <div className="mt-3 shrink-0 flex flex-wrap items-center gap-x-6 gap-y-3 border-b pb-3" style={{ borderColor: "var(--border)" }}>
        <Check checked={query.reachable} onChange={(v) => set({ reachable: v })}
               title="Hides roles ruled out for you: a visa they won't sponsor, a language you don't list, remote only for other countries">
          Only roles I can take
        </Check>
        <Check checked={query.visa} onChange={(v) => set({ visa: v })}>Says it sponsors a visa</Check>
        <Check checked={query.reliable} onChange={(v) => set({ reliable: v })}
               title="Hides recruiting-agency posts and postings with scam warning signs">
          Only reliable employers
        </Check>
        <div className="ml-auto flex items-center gap-4 text-sm">
          {!isDefault && (
            <button type="button" onClick={() => { setDraft(""); set(EMPTY_QUERY); }}
                    className="underline underline-offset-4" style={{ color: "var(--text-muted)" }}>
              Clear
            </button>
          )}
          <span style={{ color: "var(--text-muted)" }}>Sort</span>
          {(["score", "newest"] as const).map((s) => (
            <button key={s} type="button" aria-pressed={query.sort === s} onClick={() => set({ sort: s })}
                    style={{ color: query.sort === s ? "var(--text-primary)" : "var(--text-muted)", fontWeight: query.sort === s ? 600 : 400 }}>
              {s === "score" ? "Best for you" : "Newest"}
            </button>
          ))}
        </div>
      </div>

      {/* Count */}
      <p className="mt-3 shrink-0 text-sm" style={{ color: "var(--text-muted)" }} aria-live="polite">
        {data ? (
          <>
            <span style={{ color: "var(--text-secondary)" }}>{data.total.toLocaleString()} {data.total === 1 ? "role" : "roles"}</span>
            {countryName ? ` in or open to ${countryName}` : ""}
            {data.capped ? " · from the newest 600 postings: add a word or a filter to reach older ones" : ""}
          </>
        ) : results.error && !loading ? null : "Searching…"}
      </p>
      {decisionError && <p className="mt-2 text-sm" role="alert" style={{ color: "var(--danger)" }}>{decisionError}</p>}

      {results.error && !loading ? (
        <div className="flex-1 py-20 text-center max-w-md mx-auto">
          <p className="font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>The search didn&apos;t go through.</p>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>Try again in a moment.</p>
        </div>
      ) : data && jobs.length === 0 ? (
        <div className="flex-1 py-20 text-center max-w-md mx-auto">
          <p className="font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>Nothing matches.</p>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            {query.reachable ? "Try fewer filters, or untick “Only roles I can take” to see everything." : "Try fewer words or filters."}
          </p>
        </div>
      ) : (
        <div className={`mt-3 lg:flex-1 lg:min-h-0 grid grid-cols-1 lg:grid-cols-[360px_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-6 transition-opacity ${loading ? "opacity-60" : ""}`}>
          <div className="max-h-[60vh] lg:max-h-none lg:min-h-0 overflow-y-auto custom-scrollbar -mx-1 px-1 space-y-1 pr-2">
            {!data && [0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="h-[68px] rounded-lg skeleton-shimmer" />)}
            {jobs.map((opp: SearchResult) => (
              <OpportunityCardCompact key={opp.url} opp={opp} selected={selected?.url === opp.url} onClick={() => setSelectedUrl(opp.url)} />
            ))}
            {data && jobs.length < data.total && (
              <button type="button" onClick={loadMore} disabled={more}
                      className="w-full py-3 text-sm disabled:opacity-50" style={{ color: "var(--accent)" }}>
                {more ? "Loading…" : `Show more (${(data.total - jobs.length).toLocaleString()} left)`}
              </button>
            )}
          </div>
          <div className="rounded-2xl border overflow-hidden lg:min-h-0 h-[80vh] lg:h-auto" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            {selected && (
              <OpportunityDetailPanel
                key={selected.url}
                opp={selected}
                busy={busy}
                scoredNow={!selected.in_opportunities}
                onApply={() => handleDecision(selected.url, "applied")}
                onShortlist={() => handleDecision(selected.url, "to_apply")}
                onSkip={() => handleDecision(selected.url, "skipped")}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
