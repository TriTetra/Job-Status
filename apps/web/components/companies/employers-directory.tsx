"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { fetchEmployers, type EmployersDirectory } from "@/features/companies/employers";
import { safeHttpUrl } from "@/lib/utils";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

/**
 * The main employers of software people in a country, each with a link to its own careers page.
 * Where Aplio reads the employer's jobs, the row says so and opens its company page here.
 */
export function EmployersDirectoryView({ query, onOpenBoard }: { query: string; onOpenBoard: (key: string) => void }) {
  const [data, setData] = useState<EmployersDirectory | null>(null);
  const [error, setError] = useState(false);
  const [sector, setSector] = useState<string | null>(null);
  const [onlyTracked, setOnlyTracked] = useState(false);

  useEffect(() => {
    fetchEmployers("tr").then(setData).catch(() => setError(true));
  }, []);

  const groups = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    const shown = data.employers
      .filter((e) => !sector || e.sector === sector)
      .filter((e) => !onlyTracked || e.tracked)
      .filter((e) => !q || `${e.name} ${e.city ?? ""} ${e.sector}`.toLowerCase().includes(q));
    return data.sectors
      .map((s) => ({ ...s, items: shown.filter((e) => e.sector === s.id) }))
      .filter((g) => g.items.length > 0);
  }, [data, query, sector, onlyTracked]);

  if (error) return <p className="py-16 text-center text-sm" style={{ color: "var(--text-muted)" }}>The directory couldn&apos;t be loaded.</p>;
  if (!data) return <div className="mt-4 grid sm:grid-cols-2 xl:grid-cols-3 gap-3">{[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="h-14 rounded-lg skeleton-shimmer" />)}</div>;

  return (
    <div className="mt-4 lg:flex-1 lg:min-h-0 flex flex-col">
      <div className="shrink-0 flex flex-wrap items-baseline gap-x-6 gap-y-2">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          <span className="fi fi-tr rounded-[2px] mr-1.5" style={{ width: "1.25em", height: "0.94em", backgroundSize: "cover" }} aria-hidden />
          {data.count} employers of software, data and AI people in Türkiye. Aplio reads the jobs of {data.tracked};
          for the rest, their careers page is one click away.
        </p>
        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-muted)" }}>
          <input type="checkbox" checked={onlyTracked} onChange={(e) => setOnlyTracked(e.target.checked)} className="accent-[var(--accent)]" />
          Only the ones Aplio reads
        </label>
      </div>
      <nav className="mt-3 shrink-0 flex flex-wrap gap-x-4 gap-y-2" aria-label="Sectors">
        {[{ id: null as string | null, label: "All sectors" }, ...data.sectors].map((s) => (
          <button key={s.id ?? "all"} type="button" onClick={() => setSector(s.id)} aria-pressed={sector === s.id}
                  className="text-sm py-0.5 border-b-2"
                  style={{ color: sector === s.id ? "var(--text-primary)" : "var(--text-muted)", fontWeight: sector === s.id ? 600 : 400,
                           borderColor: sector === s.id ? "var(--accent)" : "transparent" }}>
            {s.label}
          </button>
        ))}
      </nav>

      <div className="mt-4 lg:flex-1 lg:min-h-0 overflow-y-auto custom-scrollbar pr-2 space-y-7">
        {groups.map((g) => (
          <section key={g.id}>
            <p className={LABEL} style={LABEL_STYLE}>{g.label} · {g.items.length}</p>
            <ul className="mt-2 grid sm:grid-cols-2 xl:grid-cols-3 gap-x-6">
              {g.items.map((e) => {
                const href = safeHttpUrl(e.careers_url);
                return (
                  <li key={e.name} className="flex items-center gap-3 py-2.5 border-b" style={{ borderColor: "var(--border)" }}>
                    <CompanyLogo name={e.name} companyKey={e.board_key} domain={e.domain} size={34} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>{e.name}</p>
                      <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                        {e.city ?? "Türkiye"}
                        {e.tracked && e.board_key && (
                          <button type="button" onClick={() => onOpenBoard(e.board_key!)} className="ml-1.5 hover:underline underline-offset-2"
                                  style={{ color: "var(--success)" }}>
                            · Aplio reads its jobs{e.open_roles ? ` (${e.open_roles} open in Türkiye)` : ""}
                          </button>
                        )}
                      </p>
                    </div>
                    {href && (
                      <a href={href} target="_blank" rel="noopener noreferrer"
                         className="shrink-0 inline-flex items-center gap-0.5 text-xs px-2.5 py-1 rounded-full border hover:bg-[var(--surface-hover)]"
                         style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                        Careers <ArrowUpRight className="h-3 w-3" />
                      </a>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
        {groups.length === 0 && <p className="py-10 text-sm" style={{ color: "var(--text-muted)" }}>No employer matches.</p>}
        <p className="pb-4 text-[11px] leading-relaxed max-w-[720px]" style={{ color: "var(--text-muted)" }}>
          Links go to each employer&apos;s own careers page. Aplio only reads jobs where the employer publishes them through
          a job system with a public feed; many post only on their own site, Kariyer.net or LinkedIn, whose terms don&apos;t allow
          automated collection.
        </p>
      </div>
    </div>
  );
}
