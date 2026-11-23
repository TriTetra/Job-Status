"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { safeHttpUrl } from "@/lib/utils";

/** GET /api/companies/card (careeros/companies/facts.py). */
interface CompanyFacts {
  name: string;
  domain: string | null;
  wikidata: {
    id: string; label: string; description: string | null; founded: number | null; dissolved: number | null;
    employees: { count: number; year: number | null } | null; country: string | null; headquarters: string | null;
    industry: string[]; listed_on: string[]; parent: string | null; url: string; source: string;
  } | null;
  companies_house: {
    number: string; name: string; status: string; incorporated: string | null; type: string | null;
    url: string; source: string;
  } | null;
  companies_house_on: boolean;
  people: {
    comments: number; search: string; source: string;
    points?: { text: string; sources: string[] }[];
    links?: { url: string; at: string }[];
  } | null;
  news: { type: string; title: string; url: string | null; source: string; date: string | null; count?: number }[];
  good: string[];
  concerns: string[];
}

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const NEWS_WORD: Record<string, string> = { layoff: "Layoffs", funding: "Funding", acquisition: "Acquisition" };

function Source({ href, children }: { href: string; children: React.ReactNode }) {
  const safe = safeHttpUrl(href);
  if (!safe) return <>{children}</>;
  return (
    <a href={safe} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 underline underline-offset-2"
       style={{ color: "var(--text-muted)" }}>
      {children} <ArrowUpRight className="h-3 w-3" />
    </a>
  );
}

const params = (name: string, domain?: string | null, uk?: boolean) =>
  new URLSearchParams({ name, ...(domain ? { domain } : {}), ...(uk ? { uk: "true" } : {}) }).toString();

/** The employer on the public record: Wikidata, the UK register, news, and what people on Hacker News say. */
export function CompanyCard({ company, domain, uk = false }: { company: string; domain?: string | null; uk?: boolean }) {
  const [f, setF] = useState<CompanyFacts | null>(null);
  const [loading, setLoading] = useState(true);
  const [reading, setReading] = useState(false);

  useEffect(() => {
    let live = true;
    apiFetch<CompanyFacts>(`/api/companies/card?${params(company, domain, uk)}`)
      .then((d) => live && setF(d))
      .catch(() => live && setF(null))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [company, domain, uk]);

  const readPeople = async () => {
    setReading(true);
    try {
      setF(await apiFetch<CompanyFacts>(`/api/companies/card/people?${params(company, domain)}`, { method: "POST" }));
    } finally {
      setReading(false);
    }
  };

  if (loading) return <p className="text-xs" style={{ color: "var(--text-muted)" }}>Reading the public record…</p>;
  if (!f) return null;
  const w = f.wikidata;
  const ch = f.companies_house;
  const facts = w ? [
    w.founded ? `Founded ${w.founded}` : null,
    w.dissolved ? `dissolved ${w.dissolved}` : null,
    w.employees ? `${w.employees.count.toLocaleString()} employees${w.employees.year ? ` (${w.employees.year})` : ""}` : null,
    w.headquarters ? `HQ ${w.headquarters}${w.country && w.country !== w.headquarters ? `, ${w.country}` : ""}` : null,
    w.industry.length ? w.industry.join(", ") : null,
    w.listed_on.length ? `listed on ${w.listed_on.join(", ")}` : null,
    w.parent ? `part of ${w.parent}` : null,
  ].filter(Boolean) : [];

  return (
    <section>
      <p className={LABEL} style={LABEL_STYLE}>On the public record</p>
      <div className="mt-2 space-y-2 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {facts.length > 0 ? (
          <p>{facts.join(" · ")} · <Source href={w!.url}>Wikidata</Source></p>
        ) : (
          <p style={{ color: "var(--text-muted)" }}>
            {f.domain ? "Not on Wikidata under its website." : "No website known, so Wikidata isn't matched (namesakes are never guessed)."}
          </p>
        )}
        {ch && (
          <p>
            UK register: <span style={{ color: ch.status === "active" ? "var(--text-primary)" : "var(--danger)" }}>{ch.status.replace(/-/g, " ")}</span>
            {ch.incorporated ? ` since ${ch.incorporated.slice(0, 4)}` : ""} · <Source href={ch.url}>Companies House</Source>
          </p>
        )}
        {f.news.map((n) => (
          <p key={`${n.type}-${n.date}-${n.title}`}>
            <span style={{ color: n.type === "layoff" ? "var(--danger)" : "var(--text-primary)" }}>{NEWS_WORD[n.type] ?? n.type}</span>
            {n.date ? ` · ${n.date}` : ""}: {n.url ? <Source href={n.url}>{n.title}</Source> : n.title}
          </p>
        ))}
        {f.concerns.length > 0 && (
          <p style={{ color: "var(--danger)" }}>Counts against trust: {f.concerns.join("; ")}.</p>
        )}
      </div>

      <p className={`${LABEL} mt-5`} style={LABEL_STYLE}>On Hacker News</p>
      <div className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {!f.people ? (
          <button onClick={readPeople} disabled={reading} className="inline-flex items-center gap-1.5 underline underline-offset-4 disabled:opacity-50"
                  style={{ color: "var(--accent)" }}>
            {reading && <Loader2 className="h-3 w-3 animate-spin" />}
            {reading ? "Reading comments…" : "What do people there say about working at it?"}
          </button>
        ) : f.people.points && f.people.points.length > 0 ? (
          <ul className="space-y-1.5">
            {f.people.points.map((p) => (
              <li key={p.text}>
                {p.text}{" "}
                {p.sources.map((u, i) => (
                  <a key={u} href={safeHttpUrl(u) ?? undefined} target="_blank" rel="noopener noreferrer"
                     className="font-mono text-[10px] align-super ml-0.5 underline" style={{ color: "var(--accent)" }}>{i + 1}</a>
                ))}
              </li>
            ))}
          </ul>
        ) : f.people.links && f.people.links.length > 0 ? (
          <p>
            The summary isn&apos;t available right now; the comments:{" "}
            {f.people.links.map((l, i) => (
              <a key={l.url} href={safeHttpUrl(l.url) ?? undefined} target="_blank" rel="noopener noreferrer"
                 className="underline underline-offset-2 mr-2" style={{ color: "var(--accent)" }}>{l.at || `#${i + 1}`}</a>
            ))}
          </p>
        ) : (
          <p style={{ color: "var(--text-muted)" }}>
            {f.people.comments ? `Only ${f.people.comments} comment${f.people.comments === 1 ? "" : "s"} about working there: too few to sum up.`
              : "Little discussion about working there."}
          </p>
        )}
        {f.people && (
          <p className="mt-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
            {f.people.points?.length
              ? `Summarised from ${f.people.comments} Hacker News comments; each point links to its comments.`
              : `From ${f.people.comments} Hacker News comments that name the company.`}{" "}
            <Source href={f.people.search}>Search them yourself</Source>
          </p>
        )}
      </div>
    </section>
  );
}
