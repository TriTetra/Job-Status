"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { BoardCompany } from "@/features/companies/board-types";
import { TREND, fitLine, profileLine, weekLine } from "@/features/companies/format";

type View = "fits" | "hiring" | "all";

/** The companies CareerOS reads a job board for — sorted by what they mean for you. */
export function CompaniesView({ companies }: { companies: BoardCompany[] }) {
  const fits = companies.filter((c) => c.your_matches > 0);
  const [view, setView] = useState<View>(fits.length ? "fits" : "all");
  const [query, setQuery] = useState("");

  const hiringFaster = companies.filter((c) => c.trend === "spike" || c.trend === "up").length;
  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return companies
      .filter((c) => (view === "fits" ? c.your_matches > 0 : view === "hiring" ? c.new_this_week > 0 : true))
      .filter((c) => !q || c.name.toLowerCase().includes(q));
  }, [companies, view, query]);

  const views: Array<{ id: View; label: string; n: number }> = [
    { id: "fits", label: "Fit you", n: fits.length },
    { id: "hiring", label: "Posted this week", n: companies.filter((c) => c.new_this_week > 0).length },
    { id: "all", label: "All", n: companies.length },
  ];

  return (
    <div className="wide-container px-6 lg:px-8 py-10 max-w-[1100px]">
      <h1 className="font-serif-display text-4xl" style={{ color: "var(--text-primary)" }}>Companies</h1>
      <p className="mt-3 text-base max-w-[720px]" style={{ color: "var(--text-secondary)" }}>
        {fits.length} of the {companies.length} companies we read job boards for have roles that fit you
        {hiringFaster ? `; ${hiringFaster} are posting faster than last week` : ""}.
      </p>

      <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 border-b pb-3" style={{ borderColor: "var(--border)" }}>
        <nav className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Views">
          {views.map((v) => (
            <button key={v.id} onClick={() => setView(v.id)} aria-current={v.id === view ? "page" : undefined}
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
        <p className="py-16 text-center text-sm" style={{ color: "var(--text-muted)" }}>No companies in this view.</p>
      ) : (
        <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
          {shown.map((c) => {
            const fit = fitLine(c);
            const profile = profileLine(c);
            const trend = TREND[c.trend];
            return (
              <li key={c.key} style={{ borderColor: "var(--border)" }}>
                <Link href={`/companies/${encodeURIComponent(c.key)}`}
                      className="grid grid-cols-[minmax(0,1fr)_auto] md:grid-cols-[minmax(0,1.3fr)_5.5rem_minmax(0,1fr)_minmax(0,1.3fr)] gap-x-6 gap-y-1 py-5 group">
                  <div className="min-w-0">
                    <p className="text-base font-semibold group-hover:underline underline-offset-4" style={{ color: "var(--text-primary)" }}>{c.name}</p>
                    {profile && <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>{profile}</p>}
                    {fit && <p className="text-sm mt-1" style={{ color: "var(--accent)" }}>{fit}</p>}
                  </div>
                  <div className="text-right md:text-left">
                    <p className="font-serif-display text-3xl tabular-nums leading-none" style={{ color: "var(--text-primary)" }}>{c.open_roles}</p>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>open roles</p>
                  </div>
                  <div className="col-span-2 md:col-span-1 text-sm">
                    <p style={{ color: trend.color }}>{trend.label}</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{weekLine(c)}</p>
                  </div>
                  <div className="col-span-2 md:col-span-1 text-sm min-w-0">
                    {c.top_skills.length > 0 ? (
                      <>
                        <p className="truncate" style={{ color: "var(--text-secondary)" }}>
                          {c.top_skills.slice(0, 4).map((s, i) => (
                            <span key={s.name} style={{ color: s.you_show ? "var(--success)" : "var(--text-secondary)" }}>
                              {i > 0 && <span style={{ color: "var(--text-muted)" }}> · </span>}
                              {s.name}
                            </span>
                          ))}
                        </p>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                          you show {c.skills_you_show} of the {c.top_skills.length} they ask for most
                        </p>
                      </>
                    ) : (
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{c.sync_error ? "board couldn't be read lately" : "no open roles in your field"}</p>
                    )}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
