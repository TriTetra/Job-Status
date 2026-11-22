import Link from "next/link";
import { notFound, unstable_rethrow } from "next/navigation";
import { ArrowUpRight, Check, X } from "lucide-react";
import { ApiError } from "@/lib/api/server";
import { safeHttpUrl } from "@/lib/utils";
import { getBoardCompany } from "@/features/companies/board-server";
import { TREND, profileLine, weekLine } from "@/features/companies/format";

const LABEL = "text-[11px] uppercase tracking-[0.08em] mb-5";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const REC_COLOR: Record<string, string> = { APPLY: "var(--success)", CONSIDER: "var(--accent)", SKIP: "var(--text-muted)" };

function ago(iso: string | null): string | null {
  if (!iso) return null;
  const days = Math.floor((Date.now() - Date.parse(iso)) / 86_400_000);
  return days <= 0 ? "today" : days === 1 ? "1 day ago" : days < 30 ? `${days} days ago` : `${Math.floor(days / 30)} mo ago`;
}

export default async function CompanyPage({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  let c;
  try {
    c = await getBoardCompany(decodeURIComponent(name));
  } catch (err) {
    unstable_rethrow(err);
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }
  const trend = TREND[c.trend];
  const profile = profileLine(c);
  const stats = [
    { value: String(c.open_roles), label: "open roles in your field" },
    { value: c.new_this_week ? `+${c.new_this_week}` : "0", label: weekLine(c), note: trend.label, color: trend.color },
    { value: String(c.your_matches), label: c.your_strong ? `fit you · ${c.your_strong} strong` : "fit you" },
    { value: c.remote_share != null ? `${Math.round(c.remote_share * 100)}%` : "—", label: "remote" },
  ];

  return (
    <div className="max-w-[920px] mx-auto px-6 lg:px-10 py-14">
      <Link href="/companies" className="text-sm" style={{ color: "var(--text-muted)" }}>← Companies</Link>
      <h1 className="mt-4 font-serif-display text-5xl" style={{ color: "var(--text-primary)" }}>{c.name}</h1>
      {profile && <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>{profile}</p>}

      <dl className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-8">
        {stats.map((s) => (
          <div key={s.label}>
            <dd className="font-serif-display text-4xl tabular-nums" style={{ color: s.color ?? "var(--text-primary)" }}>{s.value}</dd>
            <dt className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>{s.label}</dt>
            {s.note && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{s.note}</p>}
          </div>
        ))}
      </dl>

      {c.top_skills.length > 0 && (
        <section className="pt-12 mt-12 border-t" style={{ borderColor: "var(--border)" }}>
          <div className={LABEL} style={LABEL_STYLE}>What they ask for most</div>
          <ul className="grid sm:grid-cols-2 gap-x-10 gap-y-3">
            {c.top_skills.map((s) => (
              <li key={s.name} className="flex items-center justify-between gap-4 text-sm">
                <span className="inline-flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                  {s.you_show ? <Check className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="you show it" />
                    : <X className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--danger)" }} aria-label="not in your evidence" />}
                  {s.name}
                </span>
                <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>{s.jobs} roles</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="pt-12 mt-12 border-t" style={{ borderColor: "var(--border)" }}>
        <div className={LABEL} style={LABEL_STYLE}>Open roles · {c.roles.length}</div>
        {c.roles.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>No open roles in your field right now.</p>
        ) : (
          <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
            {c.roles.map((r) => {
              const href = r.score != null ? `/inbox?job=${encodeURIComponent(r.url)}` : null;
              const posting = safeHttpUrl(r.application_url);
              return (
                <li key={r.url} className="py-4 grid grid-cols-[minmax(0,1fr)_auto] gap-4" style={{ borderColor: "var(--border)" }}>
                  <div className="min-w-0">
                    <p className="text-base" style={{ color: "var(--text-primary)" }}>{r.title}</p>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                      {[r.remote ? "Remote" : r.location, ago(r.posted_at) && `posted ${ago(r.posted_at)}`, r.skills.slice(0, 4).join(" · ")].filter(Boolean).join(" · ")}
                    </p>
                  </div>
                  <div className="text-right text-sm whitespace-nowrap">
                    {r.score != null && href ? (
                      <Link href={href} className="font-mono font-semibold" style={{ color: REC_COLOR[r.recommendation ?? ""] ?? "var(--text-secondary)" }}>
                        {r.score} →
                      </Link>
                    ) : posting ? (
                      <a href={posting} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
                        Posting <ArrowUpRight className="h-3.5 w-3.5" />
                      </a>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {c.last_synced_at && (
        <p className="mt-12 text-xs" style={{ color: "var(--text-muted)" }}>
          Read from {c.name}&apos;s {c.ats} board · last read {ago(c.last_synced_at)}.
        </p>
      )}
    </div>
  );
}
