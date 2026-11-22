"use client";

import Link from "next/link";
import { ArrowUpRight, Check, X } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { safeHttpUrl } from "@/lib/utils";
import type { BoardCompanyDetail } from "@/features/companies/board-types";
import { TREND, profileLine, weekLine } from "@/features/companies/format";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const REC_COLOR: Record<string, string> = { APPLY: "var(--success)", CONSIDER: "var(--accent)", SKIP: "var(--text-muted)" };

function ago(iso: string | null): string | null {
  if (!iso) return null;
  const days = Math.floor((Date.now() - Date.parse(iso)) / 86_400_000);
  return days <= 0 ? "today" : days === 1 ? "1 day ago" : days < 30 ? `${days} days ago` : `${Math.floor(days / 30)} mo ago`;
}

/** Eight weeks of new postings as quiet bars; this week in the accent. */
function WeeklyBars({ weeks }: { weeks: number[] }) {
  const max = Math.max(1, ...weeks);
  return (
    <div>
      <div className="flex items-end gap-1.5 h-14" role="img" aria-label={`New postings per week: ${weeks.join(", ")}`}>
        {weeks.map((n, i) => (
          <div key={i} className="flex-1 rounded-sm" title={`${n} new`}
               style={{ height: n ? `${Math.max(8, (n / max) * 100)}%` : "2px", background: i === weeks.length - 1 ? "var(--accent)" : "rgba(238,233,223,0.18)" }} />
        ))}
      </div>
      <div className="mt-1.5 flex justify-between text-[10px]" style={{ color: "var(--text-muted)" }}>
        <span>8 weeks ago</span><span>this week</span>
      </div>
    </div>
  );
}

/** One company: who, how fast it hires, what it asks for, and its open roles by your fit. */
export function CompanyPanel({ c }: { c: BoardCompanyDetail }) {
  const trend = TREND[c.trend];
  const profile = profileLine(c);
  const stats = [
    { value: String(c.open_roles), label: "open roles in your field" },
    { value: String(c.your_matches), label: c.your_strong ? `fit you · ${c.your_strong} strong` : "fit you" },
    { value: c.remote_share != null ? `${Math.round(c.remote_share * 100)}%` : "—", label: "remote" },
  ];

  return (
    <div className="h-full flex flex-col min-h-0">
      <header className="px-8 pt-7 pb-6 [@media(max-height:820px)]:pt-5 [@media(max-height:820px)]:pb-4 border-b shrink-0" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-start gap-4">
          <CompanyLogo name={c.name} companyKey={c.key} size={56} />
          <div className="min-w-0 flex-1">
            <h2 className="font-serif-display text-[32px] leading-tight" style={{ color: "var(--text-primary)" }}>{c.name}</h2>
            <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
              {[profile, c.last_synced_at ? `board read ${ago(c.last_synced_at)}` : null].filter(Boolean).join(" · ")}
            </p>
          </div>
        </div>
        <div className="mt-6 [@media(max-height:820px)]:mt-4 grid grid-cols-[repeat(3,minmax(0,1fr))_minmax(0,1.4fr)] gap-x-6 gap-y-5 items-end">
          {stats.map((s) => (
            <div key={s.label}>
              <p className="font-serif-display text-[34px] leading-none tabular-nums" style={{ color: "var(--text-primary)" }}>{s.value}</p>
              <p className="mt-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>{s.label}</p>
            </div>
          ))}
          <div className="col-span-3 sm:col-span-1">
            {c.weekly_new?.length ? <WeeklyBars weeks={c.weekly_new} /> : null}
            <p className="mt-1 text-xs"><span style={{ color: trend.color }}>{trend.label}</span>
              <span style={{ color: "var(--text-muted)" }}> · {weekLine(c)}</span></p>
          </div>
        </div>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-8 py-6 grid xl:grid-cols-[minmax(0,1fr)_240px] gap-x-10 gap-y-8 content-start">
        <section className="min-w-0 order-2 xl:order-1">
          <p className={LABEL} style={LABEL_STYLE}>Open roles · {c.roles.length}</p>
          {c.roles.length === 0 ? (
            <p className="mt-3 text-sm" style={{ color: "var(--text-muted)" }}>No open roles in your field right now.</p>
          ) : (
            <ul className="mt-2">
              {c.roles.map((r) => {
                const href = r.score != null ? `/inbox?job=${encodeURIComponent(r.url)}` : null;
                const posting = safeHttpUrl(r.application_url);
                const meta = [r.remote ? "Remote" : r.location, ago(r.posted_at)].filter(Boolean).join(" · ");
                const body = (
                  <>
                    <div className="min-w-0">
                      <p className="text-[15px] leading-snug" style={{ color: "var(--text-primary)" }}>{r.title}</p>
                      <p className="text-xs mt-1 truncate" style={{ color: "var(--text-muted)" }}>
                        {meta}{r.skills.length ? ` · ${r.skills.slice(0, 4).join(" · ")}` : ""}
                      </p>
                    </div>
                    <span className="font-mono text-sm font-semibold tabular-nums shrink-0" style={{ color: REC_COLOR[r.recommendation ?? ""] ?? "var(--text-muted)" }}>
                      {r.score != null ? r.score : <ArrowUpRight className="h-4 w-4" />}
                    </span>
                  </>
                );
                const cls = "flex items-center justify-between gap-4 py-3 border-b -mx-3 px-3 rounded-md hover:bg-[rgba(44,59,77,0.5)] transition-colors";
                return (
                  <li key={r.url}>
                    {href ? (
                      <Link href={href} className={cls} style={{ borderColor: "var(--border)" }}>{body}</Link>
                    ) : posting ? (
                      <a href={posting} target="_blank" rel="noopener noreferrer" className={cls} style={{ borderColor: "var(--border)" }}>{body}</a>
                    ) : (
                      <div className={cls} style={{ borderColor: "var(--border)" }}>{body}</div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {c.top_skills.length > 0 && (
          <aside className="order-1 xl:order-2">
            <p className={LABEL} style={LABEL_STYLE}>What they ask for</p>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>you show {c.skills_you_show} of {c.top_skills.length}</p>
            <ul className="mt-3 grid grid-cols-2 xl:grid-cols-1 gap-x-6 gap-y-2.5">
              {c.top_skills.map((s) => (
                <li key={s.name} className="flex items-center justify-between gap-3 text-sm">
                  <span className="inline-flex items-center gap-2 min-w-0" style={{ color: "var(--text-primary)" }}>
                    {s.you_show ? <Check className="h-3.5 w-3.5 shrink-0" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="you show it" />
                      : <X className="h-3.5 w-3.5 shrink-0" strokeWidth={2.5} style={{ color: "var(--danger)" }} aria-label="not in your evidence" />}
                    <span className="truncate">{s.name}</span>
                  </span>
                  <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>{s.jobs}</span>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </div>
  );
}
