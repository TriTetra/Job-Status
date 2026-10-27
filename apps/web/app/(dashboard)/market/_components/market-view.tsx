"use client";

import { useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  Zap,
  RefreshCw,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { DEFAULT_RANGE, loadMarketSnapshot } from "@/features/market/snapshot";
import type { MarketSignal, MarketSnapshot, MarketSummary, SkillTrend, TimeRange } from "@/features/market/types";

export function MarketView({ initial }: { initial: MarketSnapshot }) {
  const [summary, setSummary] = useState<MarketSummary | null>(initial.summary);
  const [signals, setSignals] = useState<MarketSignal[]>(initial.signals);
  const [trends, setTrends] = useState<SkillTrend[]>(initial.trends);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRangeState] = useState<TimeRange>(DEFAULT_RANGE);
  const [refreshing, setRefreshing] = useState(false);

  // First render uses the server snapshot; range changes and refreshes fetch from the browser
  const loadData = async (range: TimeRange) => {
    setLoading(true);
    try {
      const snap = await loadMarketSnapshot(apiFetch, range);
      setSummary(snap.summary);
      setSignals(snap.signals);
      setTrends(snap.trends);
    } catch (err) {
      console.error("[market] load failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const setTimeRange = (range: TimeRange) => {
    setTimeRangeState(range);
    void loadData(range);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await apiFetch(`/api/market/refresh`, { method: "POST" });
      setTimeout(() => loadData(timeRange), 3000);
    } catch (err) {
      console.error("[market] refresh failed:", err);
    } finally {
      setTimeout(() => setRefreshing(false), 2000);
    }
  };

  const formatImpact = (impact: string) => {
    if (impact === "high") return { label: "HIGH", color: "var(--warning)" };
    if (impact === "medium") return { label: "MED", color: "var(--text-secondary)" };
    return { label: "LOW", color: "var(--text-muted)" };
  };

  const SignalIcon = ({ type }: { type: string }) => {
    if (type === "hiring_spike")
      return <TrendingUp className="h-3.5 w-3.5" style={{ color: "var(--success)" }} />;
    if (type === "layoff")
      return <TrendingDown className="h-3.5 w-3.5" style={{ color: "var(--danger)" }} />;
    if (type === "funding" || type === "funding_round")
      return <Zap className="h-3.5 w-3.5" style={{ color: "var(--accent)" }} />;
    return <Minus className="h-3.5 w-3.5" style={{ color: "var(--text-muted)" }} />;
  };

  const totalSignals = summary
    ? Object.values(summary.signal_counts).reduce((a, b) => a + b, 0)
    : 0;

  const rangeLabel =
    timeRange === "7d" ? "week" : timeRange === "30d" ? "month" : "quarter";

  return (
    <div className="narrative-container px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-10">
        <NarrativeText size="3xl" weight="semibold" as="h1" className="mb-2">
          Market Intelligence
        </NarrativeText>
        <p className="text-base" style={{ color: "var(--text-secondary)" }}>
          {loading
            ? "Loading signals…"
            : `${totalSignals} signals in the last ${rangeLabel}`}
        </p>
      </div>

      {/* Controls */}
      <div
        className="flex items-center justify-between mb-8 pb-6 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-1">
          {(["7d", "30d", "90d"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className="px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer"
              style={{
                background: timeRange === r ? "var(--surface)" : "transparent",
                color: timeRange === r ? "var(--text-primary)" : "var(--text-muted)",
              }}
            >
              {r}
            </button>
          ))}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`}
          />
          {refreshing ? "Refreshing…" : "Refresh"}
        </Button>
      </div>

      {loading ? (
        <div className="py-24 text-center">
          <Loader2
            className="h-6 w-6 animate-spin mx-auto mb-3"
            style={{ color: "var(--text-muted)" }}
          />
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Loading market signals…
          </p>
        </div>
      ) : (
        <>
          {/* Summary grid */}
          <div
            className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12 pb-12 border-b"
            style={{ borderColor: "var(--border)" }}
          >
            {/* Signal breakdown */}
            <div>
              <div
                className="text-[11px] font-semibold tracking-wider uppercase mb-4"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
              >
                Signal Breakdown
              </div>
              <div className="space-y-2">
                {summary &&
                  Object.entries(summary.signal_counts).map(([type, count], i) => (
                    <div
                      key={`sig-${type}-${i}`}
                      className="flex items-center justify-between"
                    >
                      <span
                        className="text-sm capitalize"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {type.replace(/_/g, " ")}
                      </span>
                      <span
                        className="text-sm font-semibold tabular-nums"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {count}
                      </span>
                    </div>
                  ))}
                {(!summary ||
                  Object.keys(summary.signal_counts).length === 0) && (
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No signals
                  </p>
                )}
              </div>
            </div>

            {/* Hottest companies */}
            <div>
              <div
                className="text-[11px] font-semibold tracking-wider uppercase mb-4"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
              >
                Hottest Companies
              </div>
              <div className="space-y-2">
                {summary?.top_companies.slice(0, 5).map((c, i) => (
                  <div
                    key={`co-${c.name ?? i}-${i}`}
                    className="flex items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Building2
                        className="h-3.5 w-3.5 shrink-0"
                        style={{ color: "var(--text-muted)" }}
                      />
                      <span
                        className="text-sm truncate"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {c.name}
                      </span>
                    </div>
                    <span
                      className="text-sm font-semibold tabular-nums shrink-0"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {c.count}
                    </span>
                  </div>
                ))}
                {!summary?.top_companies.length && (
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No data
                  </p>
                )}
              </div>
            </div>

            {/* Trending skills */}
            <div>
              <div
                className="text-[11px] font-semibold tracking-wider uppercase mb-4"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
              >
                Trending Skills
              </div>
              <div className="space-y-2">
                {trends.map((t, i) => (
                  <div
                    key={`trend-${t.skill}-${i}`}
                    className="flex items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {t.direction === "up" ? (
                        <TrendingUp
                          className="h-3.5 w-3.5 shrink-0"
                          style={{ color: "var(--success)" }}
                        />
                      ) : t.direction === "down" ? (
                        <TrendingDown
                          className="h-3.5 w-3.5 shrink-0"
                          style={{ color: "var(--danger)" }}
                        />
                      ) : (
                        <Minus
                          className="h-3.5 w-3.5 shrink-0"
                          style={{ color: "var(--text-muted)" }}
                        />
                      )}
                      <span
                        className="text-sm truncate"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {t.skill}
                      </span>
                    </div>
                    <span
                      className="text-sm font-semibold tabular-nums shrink-0"
                      style={{
                        color:
                          t.change_percent > 0
                            ? "var(--success)"
                            : t.change_percent < 0
                            ? "var(--danger)"
                            : "var(--text-muted)",
                      }}
                    >
                      {t.change_percent > 0 ? "+" : ""}
                      {t.change_percent.toFixed(1)}%
                    </span>
                  </div>
                ))}
                {trends.length === 0 && (
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No trend data
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Recent signals */}
          <div>
            <NarrativeText size="xl" weight="semibold" className="mb-6">
              Recent Signals
            </NarrativeText>

            {signals.length === 0 ? (
              <div className="py-16 text-center">
                <NarrativeText size="lg" weight="medium" className="mb-2">
                  No market signals yet
                </NarrativeText>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Signals will appear as we monitor hiring trends and industry news.
                </p>
              </div>
            ) : (
              <div className="space-y-0">
                {signals.map((signal) => {
                  const imp = formatImpact(signal.impact);
                  return (
                    <div
                      key={signal.id}
                      className="py-5 border-b last:border-b-0"
                      style={{ borderColor: "var(--border)" }}
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5 shrink-0">
                          <SignalIcon type={signal.signal_type} />
                        </div>
                        <div className="flex-1 min-w-0">
                          {/* Meta row */}
                          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                            <span
                              className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded"
                              style={{
                                color: imp.color,
                                background: "var(--surface)",
                              }}
                            >
                              {imp.label}
                            </span>
                            <span
                              className="text-[11px] uppercase tracking-wider"
                              style={{ color: "var(--text-muted)" }}
                            >
                              {signal.signal_type.replace(/_/g, " ")}
                            </span>
                            <span
                              className="text-[11px]"
                              style={{ color: "var(--text-muted)" }}
                            >
                              · {signal.source}
                            </span>
                          </div>

                          {/* Title — clickable if url present */}
                          {signal.url ? (
                            <a
                              href={signal.url}
                              target="_blank"
                              rel="noreferrer"
                              className="group/link inline-flex items-center gap-1.5 mb-2 hover:opacity-80 transition-opacity"
                            >
                              <span
                                className="text-base font-medium"
                                style={{ color: "var(--text-primary)" }}
                              >
                                {signal.title}
                              </span>
                              <ExternalLink
                                className="h-3.5 w-3.5 shrink-0 opacity-0 group-hover/link:opacity-60 transition-opacity"
                                strokeWidth={1.75}
                                style={{ color: "var(--text-muted)" }}
                              />
                            </a>
                          ) : (
                            <NarrativeText
                              size="base"
                              weight="medium"
                              className="mb-2"
                            >
                              {signal.title}
                            </NarrativeText>
                          )}

                          {signal.summary && (
                            <p
                              className="text-sm mb-3 leading-relaxed"
                              style={{ color: "var(--text-secondary)" }}
                            >
                              {signal.summary}
                            </p>
                          )}

                          {signal.companies_affected.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {signal.companies_affected
                                .slice(0, 3)
                                .map((co, ci) => (
                                  <span
                                    key={`${signal.id}-co-${ci}`}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium"
                                    style={{
                                      background: "var(--surface)",
                                      color: "var(--text-secondary)",
                                    }}
                                  >
                                    {co}
                                  </span>
                                ))}
                              {signal.companies_affected.length > 3 && (
                                <span
                                  className="inline-flex items-center px-2 py-0.5 rounded text-[11px]"
                                  style={{ color: "var(--text-muted)" }}
                                >
                                  +{signal.companies_affected.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        <div
                          className="text-[11px] tabular-nums shrink-0"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {new Date(signal.occurred_at).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric" }
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
