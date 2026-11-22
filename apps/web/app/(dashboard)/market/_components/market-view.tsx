"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, Check, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { loadMarket } from "@/features/market/snapshot";
import type { MarketData, OwnMarket, Period } from "@/features/market/types";

const LABEL = "text-[11px] uppercase tracking-[0.08em] mb-6";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

function money(currency: string, n: number): string {
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency, notation: "compact", maximumFractionDigits: 0 }).format(n);
  } catch {
    return String(n);
  }
}

const pct = (x: number | null | undefined) => (x == null ? "—" : `${Math.round(x * 100)}%`);

function lead(m: OwnMarket): string {
  if (m.open_matches === 0) return "No open roles match your roles yet — the boards are read every 6 hours.";
  const pace =
    m.change_pct == null
      ? ""
      : m.change_pct > 5
        ? `, ${m.change_pct}% more than the ${m.days} days before`
        : m.change_pct < -5
          ? `, ${Math.abs(m.change_pct)}% fewer than the ${m.days} days before`
          : ", about the same pace as before";
  return `${m.open_matches.toLocaleString()} open roles match yours. ${m.new_this_period} arrived in the last ${m.days} days${pace}.`;
}

/** Your market, from the postings that match your roles — then the news. */
export function MarketView({ initial }: { initial: MarketData }) {
  const [data, setData] = useState(initial);
  const [period, setPeriod] = useState<Period>(initial.own.days === 90 ? 90 : 30);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const m = data.own;
  const topGap = m.skills.filter((s) => !s.you_show).sort((a, b) => b.open_jobs - a.open_jobs)[0];

  const changePeriod = async (p: Period) => {
    setPeriod(p);
    setLoading(true);
    try {
      setData(await loadMarket(apiFetch, p));
    } finally {
      setLoading(false);
    }
  };

  // News refresh (HN + TechCrunch): wait for the job, then reload
  const refreshNews = async () => {
    setRefreshing(true);
    try {
      const { job_id } = await apiFetch<{ job_id: string }>("/api/market/refresh", { method: "POST" });
      const deadline = Date.now() + 3 * 60_000;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 2000));
        const st = await apiFetch<{ status: string }>(`/api/market/refresh/${job_id}/status`);
        if (st.status === "completed" || st.status === "failed") break;
      }
      setData(await loadMarket(apiFetch, period));
    } catch (err) {
      console.error("[market] refresh failed:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const numbers = [
    m.salary
      ? { value: money(m.salary.currency, m.salary.median), label: "median starting pay",
          note: `${money(m.salary.currency, m.salary.low)}–${money(m.salary.currency, m.salary.high)} middle half · ${m.salary.postings} postings state pay` }
      : { value: "—", label: "median starting pay", note: "too few postings state pay" },
    { value: pct(m.remote_share), label: "fully remote" },
    m.visa
      ? { value: pct(m.visa.sponsor_share), label: "sponsor visas", note: `of ${m.visa.stated} postings that say` }
      : { value: "—", label: "sponsor visas", note: "postings rarely say" },
    { value: String(m.new_this_period), label: `new in ${m.days} days`,
      note: m.change_pct == null ? undefined : `${m.change_pct >= 0 ? "+" : ""}${m.change_pct}% vs before` },
  ];

  return (
    <div className="max-w-[1000px] mx-auto px-6 lg:px-10 py-14" aria-busy={loading}>
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="font-serif-display text-4xl" style={{ color: "var(--text-primary)" }}>Market</h1>
        <div className="flex gap-4 text-sm" role="group" aria-label="Period">
          {([30, 90] as Period[]).map((p) => (
            <button key={p} onClick={() => changePeriod(p)} aria-pressed={p === period}
                    style={{ color: p === period ? "var(--text-primary)" : "var(--text-muted)", fontWeight: p === period ? 600 : 400 }}>
              {p} days
            </button>
          ))}
        </div>
      </div>
      <p className="mt-4 text-lg leading-relaxed max-w-[720px]" style={{ color: "var(--text-secondary)" }}>{lead(m)}</p>
      {topGap && (
        <p className="mt-2 text-base max-w-[720px]" style={{ color: "var(--text-secondary)" }}>
          The most asked-for skill you don&apos;t show yet is <span style={{ color: "var(--text-primary)" }}>{topGap.name}</span>
          {" "}— in {pct(topGap.share)} of these roles
          {topGap.missing_in_your_matches ? `, and missing in ${topGap.missing_in_your_matches} of your matches` : ""}.
        </p>
      )}

      <dl className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-8" style={{ opacity: loading ? 0.5 : 1 }}>
        {numbers.map((n) => (
          <div key={n.label}>
            <dd className="font-serif-display text-4xl tabular-nums" style={{ color: "var(--text-primary)" }}>{n.value}</dd>
            <dt className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>{n.label}</dt>
            {n.note && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{n.note}</p>}
          </div>
        ))}
      </dl>

      {m.skills.length > 0 && (
        <section className="pt-12 mt-12 border-t" style={{ borderColor: "var(--border)" }}>
          <div className={LABEL} style={LABEL_STYLE}>What these roles ask for</div>
          <ul className="space-y-3">
            {m.skills.map((s) => (
              <li key={s.name} className="grid grid-cols-[minmax(0,9rem)_minmax(0,1fr)_3.5rem] md:grid-cols-[12rem_minmax(0,1fr)_4rem_5rem_minmax(0,11rem)] items-center gap-x-4 gap-y-1 text-sm">
                <span className="inline-flex items-center gap-2 truncate" style={{ color: "var(--text-primary)" }}>
                  {s.you_show && <Check className="h-3.5 w-3.5 shrink-0" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="you show it" />}
                  {s.name}
                </span>
                <span className="h-[3px] rounded-full" style={{ background: "var(--border)" }} aria-hidden="true">
                  <span className="block h-full rounded-full" style={{ width: `${Math.max(2, s.share * 100)}%`, background: s.you_show ? "var(--success)" : "var(--accent)" }} />
                </span>
                <span className="font-mono text-xs tabular-nums text-right" style={{ color: "var(--text-secondary)" }}>{pct(s.share)}</span>
                <span className="hidden md:block font-mono text-xs tabular-nums" style={{ color: s.trend_pts == null ? "var(--text-muted)" : s.trend_pts > 0 ? "var(--success)" : s.trend_pts < 0 ? "var(--danger)" : "var(--text-muted)" }}>
                  {s.trend_pts == null ? "" : `${s.trend_pts > 0 ? "+" : ""}${s.trend_pts} pts`}
                </span>
                <span className="hidden md:block text-xs truncate" style={{ color: "var(--text-muted)" }}>
                  {s.you_show ? "in your evidence" : s.missing_in_your_matches ? `missing in ${s.missing_in_your_matches} of your matches` : "not in your evidence"}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-5 text-xs" style={{ color: "var(--text-muted)" }}>
            Share of open roles matching yours that require the skill; pts = change in that share vs the previous {m.days} days.
          </p>
        </section>
      )}

      {m.busiest_companies.length > 0 && (
        <section className="pt-12 mt-12 border-t" style={{ borderColor: "var(--border)" }}>
          <div className={LABEL} style={LABEL_STYLE}>Adding the most roles · last {m.days} days</div>
          <ul className="grid sm:grid-cols-2 md:grid-cols-3 gap-x-10 gap-y-3">
            {m.busiest_companies.map((c) => (
              <li key={c.name} className="flex items-baseline justify-between gap-3 text-sm">
                {c.key ? (
                  <Link href={`/companies/${encodeURIComponent(c.key)}`} style={{ color: "var(--text-primary)" }}>{c.name} →</Link>
                ) : (
                  <span style={{ color: "var(--text-primary)" }}>{c.name}</span>
                )}
                <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>+{c.new}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="pt-12 mt-12 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-baseline justify-between gap-4">
          <div className={LABEL} style={LABEL_STYLE}>In the news</div>
          <button onClick={refreshNews} disabled={refreshing} className="inline-flex items-center gap-1.5 text-xs disabled:opacity-60"
                  style={{ color: "var(--text-muted)" }}>
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Reading HN and TechCrunch…" : "Refresh"}
          </button>
        </div>
        {data.news.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>No news in this period. It&apos;s read once a day.</p>
        ) : (
          <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
            {data.news.map((n) => (
              <li key={n.id} className="py-3 grid grid-cols-[minmax(0,1fr)_auto] gap-4 text-sm" style={{ borderColor: "var(--border)" }}>
                <div className="min-w-0">
                  {n.url ? (
                    <a href={n.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1" style={{ color: "var(--text-primary)" }}>
                      {n.title} <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
                    </a>
                  ) : (
                    <span style={{ color: "var(--text-primary)" }}>{n.title}</span>
                  )}
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {n.source === "hackernews" ? "Hacker News" : n.source === "techcrunch" ? "TechCrunch" : n.source} · {n.signal_type.replace(/_/g, " ")}
                  </p>
                </div>
                <span className="text-xs whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
                  {new Date(n.occurred_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
