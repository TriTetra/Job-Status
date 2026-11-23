"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, Check, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { CompanyLogo } from "@/components/shared/company-logo";
import { loadMarket } from "@/features/market/snapshot";
import type { MarketData, OwnMarket, PayByCountry, Period } from "@/features/market/types";
import { countryName } from "@/components/ui/place-badge";
import { PayByCountrySection } from "./pay-by-country";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

function money(currency: string, n: number): string {
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency, notation: "compact", maximumFractionDigits: 0 }).format(n);
  } catch {
    return String(n);
  }
}

const pct = (x: number | null | undefined) => (x == null ? "—" : `${Math.round(x * 100)}%`);

/** The first country (targets first) with a median of stated pay: shown in its own currency. */
function headlinePay(pay: PayByCountry | null) {
  const c = pay?.countries.find((x) => x.all.median != null);
  return c && c.currency ? { code: c.code, currency: c.currency, ...c.all } : null;
}

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

function trendColor(pts: number | null): string {
  if (pts == null || pts === 0) return "var(--text-muted)";
  return pts > 0 ? "var(--success)" : "var(--danger)";
}

/** Your market on one screen: the numbers, what your roles ask for, who is adding them, the news. */
export function MarketView({ initial }: { initial: MarketData }) {
  const [data, setData] = useState(initial);
  const [period, setPeriod] = useState<Period>(initial.own.days === 90 ? 90 : 30);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const m = data.own;
  const topGap = m.skills.filter((s) => !s.you_show).sort((a, b) => b.open_jobs - a.open_jobs)[0];
  const shown = m.skills.filter((s) => s.you_show).length;
  const busiestMax = Math.max(1, ...m.busiest_companies.map((c) => c.new));
  const headline = headlinePay(data.pay);

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
    { value: String(m.new_this_period), label: `new in ${m.days} days`,
      note: m.change_pct == null ? undefined : `${m.change_pct >= 0 ? "+" : ""}${m.change_pct}% vs before`,
      noteColor: m.change_pct == null ? undefined : m.change_pct > 5 ? "var(--success)" : m.change_pct < -5 ? "var(--danger)" : undefined },
    headline
      ? { value: money(headline.currency, headline.median!), label: `median stated pay · ${countryName(headline.code)}`,
          note: `${headline.postings} tech postings state it${headline.p25 != null && headline.p75 != null
            ? ` · ${money(headline.currency, headline.p25)}–${money(headline.currency, headline.p75)} middle half` : ""}` }
      : m.salary
        ? { value: money(m.salary.currency, m.salary.median), label: "median starting pay",
            note: `${money(m.salary.currency, m.salary.low)}–${money(m.salary.currency, m.salary.high)} middle half · ${m.salary.postings} state pay` }
        : { value: "—", label: "median starting pay", note: "too few postings state pay" },
    { value: pct(m.remote_share), label: "fully remote" },
    m.visa
      ? { value: pct(m.visa.sponsor_share), label: "sponsor visas", note: `of ${m.visa.stated} postings that say` }
      : { value: "—", label: "sponsor visas", note: "postings rarely say" },
  ];

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5" aria-busy={loading}>
      {/* Masthead: the sentence, then the four numbers */}
      <header className="shrink-0 grid 2xl:grid-cols-[minmax(0,1fr)_minmax(0,720px)] gap-x-12 gap-y-6 items-end pb-6 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="min-w-0 max-w-[760px]">
          <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
            <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Market</h1>
            <div className="flex gap-4 text-sm" role="group" aria-label="Period">
              {([30, 90] as Period[]).map((p) => (
                <button key={p} onClick={() => changePeriod(p)} aria-pressed={p === period}
                        style={{ color: p === period ? "var(--text-primary)" : "var(--text-muted)", fontWeight: p === period ? 600 : 400 }}>
                  {p} days
                </button>
              ))}
            </div>
          </div>
          <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {lead(m)}
            {topGap && (
              <> The most asked-for skill you don&apos;t show yet is <span style={{ color: "var(--text-primary)" }}>{topGap.name}</span>
                {" "}— in {pct(topGap.share)} of these roles
                {topGap.missing_in_your_matches ? `, missing in ${topGap.missing_in_your_matches} of your matches` : ""}.</>
            )}
          </p>
        </div>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-10 gap-y-5 transition-opacity" style={{ opacity: loading ? 0.5 : 1 }}>
          {numbers.map((n) => (
            <div key={n.label} className="min-w-0">
              <dd className="font-serif-display text-[34px] leading-none tabular-nums" style={{ color: "var(--text-primary)" }}>{n.value}</dd>
              <dt className="mt-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>{n.label}</dt>
              {n.note && <p className="text-[11px] mt-0.5" style={{ color: n.noteColor ?? "var(--text-muted)" }}>{n.note}</p>}
            </div>
          ))}
        </dl>
      </header>

      <div className="mt-6 lg:flex-1 lg:min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-x-12 gap-y-10 transition-opacity"
           style={{ opacity: loading ? 0.5 : 1 }}>
        {/* Left: what these roles ask for */}
        <section className="lg:min-h-0 flex flex-col">
          <div className="shrink-0 flex items-baseline justify-between gap-4">
            <p className={LABEL} style={LABEL_STYLE}>What these roles ask for</p>
            {m.skills.length > 0 && (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>you show {shown} of {m.skills.length}</p>
            )}
          </div>
          {m.skills.length === 0 ? (
            <p className="mt-4 text-sm" style={{ color: "var(--text-muted)" }}>Not enough postings in this period to read skills.</p>
          ) : (
            <>
              <ul className="mt-4 lg:min-h-0 overflow-y-auto custom-scrollbar pr-2 space-y-3">
                {m.skills.map((s) => (
                  <li key={s.name} className="grid grid-cols-[minmax(0,9rem)_minmax(0,1fr)_3rem] md:grid-cols-[11rem_minmax(0,1fr)_3rem_4.5rem_minmax(0,12rem)] items-center gap-x-4 text-sm">
                    <span className="inline-flex items-center gap-2 min-w-0" style={{ color: "var(--text-primary)" }}>
                      {s.you_show
                        ? <Check className="h-3.5 w-3.5 shrink-0" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="you show it" />
                        : <span className="h-1.5 w-1.5 mx-1 shrink-0 rounded-full" style={{ background: "var(--accent)" }} aria-hidden="true" />}
                      <span className="truncate">{s.name}</span>
                    </span>
                    <span className="h-1.5 rounded-full" style={{ background: "rgba(238,233,223,0.08)" }} aria-hidden="true">
                      <span className="block h-full rounded-full" style={{ width: `${Math.max(2, s.share * 100)}%`, background: s.you_show ? "var(--success)" : "var(--accent)" }} />
                    </span>
                    <span className="font-mono text-xs tabular-nums text-right" style={{ color: "var(--text-secondary)" }}>{pct(s.share)}</span>
                    <span className="hidden md:block font-mono text-xs tabular-nums" style={{ color: trendColor(s.trend_pts) }}>
                      {s.trend_pts == null ? "" : `${s.trend_pts > 0 ? "+" : ""}${s.trend_pts} pts`}
                    </span>
                    <span className="hidden md:block text-xs truncate" style={{ color: "var(--text-muted)" }}>
                      {s.you_show ? "in your evidence" : s.missing_in_your_matches ? `missing in ${s.missing_in_your_matches} of your matches` : "not in your evidence"}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="shrink-0 mt-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
                Share of open roles matching yours that require the skill · pts = change vs the previous {m.days} days.
              </p>
            </>
          )}
        </section>

        {/* Right: who is adding roles, then the news */}
        <div className="lg:min-h-0 flex flex-col gap-8">
          {m.busiest_companies.length > 0 && (
            <section className="shrink-0">
              <p className={LABEL} style={LABEL_STYLE}>Adding the most roles · last {m.days} days</p>
              <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
                {m.busiest_companies.slice(0, 6).map((c) => {
                  const row = (
                    <>
                      <CompanyLogo name={c.name} companyKey={c.key} size={28} />
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm truncate" style={{ color: "var(--text-primary)" }}>{c.name}</span>
                        <span className="mt-1 block h-1 rounded-full" style={{ background: "rgba(238,233,223,0.08)" }} aria-hidden="true">
                          <span className="block h-full rounded-full" style={{ width: `${(c.new / busiestMax) * 100}%`, background: "var(--accent)" }} />
                        </span>
                      </span>
                      <span className="font-mono text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>+{c.new}</span>
                    </>
                  );
                  const cls = "flex items-center gap-3 py-2 -mx-2 px-2 rounded-md";
                  return (
                    <li key={c.name}>
                      {c.key ? (
                        <Link href={`/companies/${encodeURIComponent(c.key)}`} className={`${cls} hover:bg-[rgba(44,59,77,0.5)] transition-colors`}>{row}</Link>
                      ) : (
                        <div className={cls}>{row}</div>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          )}

          {data.pay && <PayByCountrySection pay={data.pay} />}

          <section className="lg:flex-1 lg:min-h-0 flex flex-col">
            <div className="shrink-0 flex items-baseline justify-between gap-4">
              <p className={LABEL} style={LABEL_STYLE}>In the news</p>
              <button onClick={refreshNews} disabled={refreshing} className="inline-flex items-center gap-1.5 text-xs disabled:opacity-60"
                      style={{ color: "var(--text-muted)" }}>
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
                {refreshing ? "Reading HN and TechCrunch…" : "Refresh"}
              </button>
            </div>
            {data.news.length === 0 ? (
              <p className="mt-3 text-sm" style={{ color: "var(--text-muted)" }}>No news in this period. It&apos;s read once a day.</p>
            ) : (
              <ul className="mt-2 lg:min-h-0 overflow-y-auto custom-scrollbar pr-2">
                {data.news.map((n) => (
                  <li key={n.id} className="py-3 border-b grid grid-cols-[minmax(0,1fr)_auto] gap-4 text-sm" style={{ borderColor: "var(--border)" }}>
                    <div className="min-w-0">
                      {n.url ? (
                        <a href={n.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-1 hover:underline" style={{ color: "var(--text-primary)" }}>
                          <span>{n.title}</span> <ArrowUpRight className="h-3.5 w-3.5 shrink-0 mt-0.5" />
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
      </div>
    </div>
  );
}
