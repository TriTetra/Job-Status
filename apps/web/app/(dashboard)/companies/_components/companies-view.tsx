"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Search } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { CompanyPanel } from "@/components/companies/company-panel";
import { cn } from "@/lib/utils";
import { fetchBoardCompany } from "@/features/companies/client";
import type { BoardCompany, BoardCompanyDetail } from "@/features/companies/board-types";
import { TREND, fitLine } from "@/features/companies/format";

type View = "fits" | "hiring" | "all";

/** The companies whose boards we read: a list on the left, the chosen one in full on the right. */
export function CompaniesView({ companies }: { companies: BoardCompany[] }) {
  const fits = companies.filter((c) => c.your_matches > 0);
  const [view, setView] = useState<View>(fits.length ? "fits" : "all");
  const [query, setQuery] = useState("");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, BoardCompanyDetail>>({});
  const [failed, setFailed] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // On phones the panel sits under the list: bring it into view when a company is picked
  const pick = (key: string) => {
    setSelectedKey(key);
    if (window.matchMedia("(max-width: 1023px)").matches) {
      requestAnimationFrame(() => panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  };

  const hiringFaster = companies.filter((c) => c.trend === "spike" || c.trend === "up").length;
  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return companies
      .filter((c) => (view === "fits" ? c.your_matches > 0 : view === "hiring" ? c.new_this_week > 0 : true))
      .filter((c) => !q || c.name.toLowerCase().includes(q));
  }, [companies, view, query]);
  const selected = shown.find((c) => c.key === selectedKey) ?? shown[0] ?? null;
  const detail = selected ? details[selected.key] : undefined;

  useEffect(() => {
    if (!selected || details[selected.key]) return;
    let live = true;
    fetchBoardCompany(selected.key)
      .then((d) => live && setDetails((all) => ({ ...all, [d.key]: d })))
      .catch(() => live && setFailed(selected.key));
    return () => {
      live = false;
    };
  }, [selected, details]);

  const views: Array<{ id: View; label: string; n: number }> = [
    { id: "fits", label: "Fit you", n: fits.length },
    { id: "hiring", label: "Posted this week", n: companies.filter((c) => c.new_this_week > 0).length },
    { id: "all", label: "All", n: companies.length },
  ];

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5">
      <div className="shrink-0 max-w-[860px]">
        <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Companies</h1>
        <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {fits.length} of the {companies.length} companies we read job boards for have roles that fit you
          {hiringFaster ? `; ${hiringFaster} are posting faster than last week` : ""}.
        </p>
      </div>

      <div className="mt-5 shrink-0 flex flex-wrap items-center gap-x-6 gap-y-3 border-b pb-3" style={{ borderColor: "var(--border)" }}>
        <nav className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Views">
          {views.map((v) => (
            <button key={v.id} onClick={() => { setView(v.id); setSelectedKey(null); }} aria-current={v.id === view ? "page" : undefined}
                    className="text-sm" style={{ color: v.id === view ? "var(--text-primary)" : "var(--text-muted)", fontWeight: v.id === view ? 600 : 400 }}>
              {v.label} <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>{v.n}</span>
            </button>
          ))}
        </nav>
        <label className="ml-auto flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
          <Search className="h-4 w-4" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Company" aria-label="Search companies"
                 className="w-40 bg-transparent border-0 border-b outline-none py-1 text-sm focus:border-[var(--accent)]"
                 style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </label>
      </div>

      {shown.length === 0 ? (
        <p className="flex-1 py-16 text-center text-sm" style={{ color: "var(--text-muted)" }}>No companies in this view.</p>
      ) : (
        <div className="mt-4 lg:flex-1 lg:min-h-0 grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-6">
          <ul className="max-h-[50vh] lg:max-h-none lg:min-h-0 overflow-y-auto custom-scrollbar space-y-1 pr-2" aria-label="Companies">
            {shown.map((c) => {
              const active = selected?.key === c.key;
              const trend = TREND[c.trend];
              const fit = fitLine(c);
              return (
                <li key={c.key}>
                  <button onClick={() => pick(c.key)} aria-current={active ? "true" : undefined}
                          className={cn("relative w-full text-left grid grid-cols-[2.5rem_minmax(0,1fr)_auto] gap-x-3 px-3 py-3 rounded-lg transition-colors",
                            active ? "bg-[var(--surface)]" : "hover:bg-[rgba(44,59,77,0.5)]")}>
                    {active && <span className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" style={{ background: "var(--accent)" }} />}
                    <CompanyLogo name={c.name} companyKey={c.key} size={40} className="mt-0.5" />
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{c.name}</span>
                      <span className="block text-xs mt-0.5 truncate" style={{ color: fit ? "var(--accent)" : "var(--text-muted)" }}>
                        {fit ?? "no matches yet"}
                      </span>
                      <span className="block text-xs mt-0.5" style={{ color: trend.color }}>{trend.label}
                        {c.new_this_week ? <span style={{ color: "var(--text-muted)" }}> · +{c.new_this_week} this week</span> : null}
                      </span>
                    </span>
                    <span className="text-right">
                      <span className="block font-serif-display text-2xl leading-none tabular-nums" style={{ color: "var(--text-primary)" }}>{c.open_roles}</span>
                      <span className="block text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>open</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          <div ref={panelRef} className="scroll-mt-4 rounded-2xl border overflow-hidden lg:min-h-0 h-[80vh] lg:h-auto" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            {detail ? (
              <CompanyPanel key={detail.key} c={detail} />
            ) : failed && failed === selected?.key ? (
              <p className="p-8 text-sm" style={{ color: "var(--text-muted)" }}>This company couldn&apos;t be loaded. Try again.</p>
            ) : (
              <div className="p-8 space-y-4" aria-busy="true">
                <div className="flex gap-4"><div className="h-14 w-14 skeleton-shimmer rounded-xl" /><div className="h-9 w-56 skeleton-shimmer rounded mt-2" /></div>
                {[80, 60, 90, 70].map((w, i) => <div key={i} className="h-4 skeleton-shimmer rounded" style={{ width: `${w}%` }} />)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
