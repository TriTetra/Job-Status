"use client";

import { useCallback, useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { StatusPill } from "@/components/ui/status-pill";
import { MetricText } from "@/components/shared/metric-text";
import { SkillTag } from "@/components/ui/skill-tag";
import { Button } from "@/components/shared/button";
import {
  Search, Plus, Building2, MapPin,
  TrendingUp, TrendingDown, Minus, Loader2,
} from "lucide-react";
import { companiesApi } from "@/features/companies/api";
import type { Company } from "@/features/companies/types";

type TierFilter = "ALL" | "big_tech" | "unicorn" | "large" | "startup";
type HiringDir = "spike" | "up" | "stable" | "down";

const TIER_LABEL: Record<string, string> = {
  big_tech: "Big Tech",
  unicorn: "Unicorn",
  large: "Large",
  startup: "Startup",
  unknown: "—",
};

const directionConfig: Record<
  HiringDir,
  { label: string; variant: "success" | "warning" | "neutral"; Icon: React.ElementType }
> = {
  spike:  { label: "SPIKE",  variant: "success", Icon: TrendingUp },
  up:     { label: "UP",     variant: "success", Icon: TrendingUp },
  stable: { label: "STABLE", variant: "neutral", Icon: Minus },
  down:   { label: "DOWN",   variant: "warning", Icon: TrendingDown },
};

export function CompaniesView({ initialCompanies }: { initialCompanies: Company[] }) {
  const [companies, setCompanies] = useState<Company[]>(initialCompanies);
  const [loading, setLoading] = useState(false);
  const [tierFilter, setTierFilter] = useState<TierFilter>("ALL");
  const [search, setSearch] = useState("");
  const [trackOpen, setTrackOpen] = useState(false);
  const [trackName, setTrackName] = useState("");
  const [tracking, setTracking] = useState(false);

  // Initial list comes from the server; this refreshes it after tracking a company
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCompanies(await companiesApi.list());
    } catch (err) {
      console.error("[companies] refresh failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTrack = async () => {
    if (!trackName.trim()) return;
    setTracking(true);
    try {
      await companiesApi.track(trackName.trim());
      setTrackOpen(false);
      setTrackName("");
      load();
    } catch (err) {
      console.error("[companies] track failed:", err);
    } finally {
      setTracking(false);
    }
  };

  const filtered = companies.filter((c) => {
    if (tierFilter !== "ALL" && c.tier !== tierFilter) return false;
    if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const hiringNow = companies.filter(
    (c) => c.hiring_trend === "up" || c.hiring_trend === "spike"
  ).length;

  return (
    <div className="wide-container px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <NarrativeText size="2xl" weight="semibold" className="mb-1">
            Companies
          </NarrativeText>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {companies.length} tracked · {hiringNow} hiring now
          </p>
        </div>
        <Button variant="outline" size="md" onClick={() => setTrackOpen((v) => !v)}>
          <Plus className="h-4 w-4" />
          Track company
        </Button>
      </div>

      {/* Track input */}
      {trackOpen && (
        <div className="mb-6 flex gap-2">
          <input
            type="text"
            value={trackName}
            onChange={(e) => setTrackName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleTrack()}
            placeholder="Company name…"
            autoFocus
            className="flex-1 max-w-sm h-9 px-3 rounded-lg text-sm outline-none transition-colors"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
            }}
          />
          <Button
            variant="primary"
            size="md"
            onClick={handleTrack}
            disabled={tracking || !trackName.trim()}
          >
            {tracking ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Add
          </Button>
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex items-center gap-3 flex-wrap">
        <div
          className="flex items-center gap-1 p-1 rounded-lg"
          style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
        >
          {(["ALL", "big_tech", "unicorn", "large", "startup"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTierFilter(t)}
              className="px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer"
              style={{
                background: tierFilter === t ? "rgba(255,177,98,0.15)" : "transparent",
                color: tierFilter === t ? "var(--accent)" : "var(--text-secondary)",
              }}
            >
              {t === "ALL" ? "ALL" : TIER_LABEL[t]}
            </button>
          ))}
        </div>
        <div className="flex-1 min-w-[200px] max-w-sm relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
            strokeWidth={1.75}
            style={{ color: "var(--text-muted)" }}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search companies..."
            className="w-full h-9 pl-9 pr-3 rounded-lg text-sm outline-none transition-colors"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
            }}
          />
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="surface p-12 text-center">
          <Loader2
            className="h-5 w-5 animate-spin mx-auto mb-3"
            style={{ color: "var(--text-muted)" }}
          />
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Loading companies…
          </p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="surface p-12 text-center">
          <NarrativeText size="lg" weight="medium" className="mb-2">
            {companies.length === 0 ? "No companies yet." : "No companies match your filters."}
          </NarrativeText>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {companies.length === 0
              ? "Track your first company to start building intelligence."
              : "Try adjusting your filters."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((company) => {
            const dir =
              directionConfig[company.hiring_trend as HiringDir] ?? directionConfig.stable;
            const DirectionIcon = dir.Icon;
            const iconColor =
              dir.variant === "success"
                ? "var(--success)"
                : dir.variant === "warning"
                ? "var(--warning)"
                : "var(--text-muted)";

            return (
              <div
                key={company.name}
                className="surface p-5 hover:bg-surface-hover transition-colors"
              >
                {/* Company header */}
                <div className="flex items-start gap-3 mb-3">
                  <div
                    className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: "rgba(255,177,98,0.12)" }}
                  >
                    <span
                      className="font-semibold text-base"
                      style={{ fontFamily: "var(--font-display)", color: "var(--accent)" }}
                    >
                      {company.name.charAt(0)}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <NarrativeText size="base" weight="semibold" className="truncate">
                      {company.name}
                    </NarrativeText>
                    <div className="mt-0.5">
                      <StatusPill
                        label={TIER_LABEL[company.tier] ?? company.tier}
                        variant="neutral"
                        size="sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Meta */}
                <div
                  className="space-y-1.5 mb-3 text-xs"
                  style={{ color: "var(--text-muted)" }}
                >
                  {company.industry && (
                    <div className="flex items-center gap-1.5">
                      <Building2 className="h-3 w-3" strokeWidth={1.75} />
                      {company.industry}
                    </div>
                  )}
                  {company.headquarters && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3" strokeWidth={1.75} />
                      {company.headquarters}
                    </div>
                  )}
                </div>

                {/* Hiring trend + open positions */}
                <div
                  className="flex items-center gap-2 mb-3 pb-3 border-b"
                  style={{ borderColor: "var(--border)" }}
                >
                  <DirectionIcon
                    className="h-3.5 w-3.5"
                    strokeWidth={2}
                    style={{ color: iconColor }}
                  />
                  <StatusPill label={dir.label} variant={dir.variant} size="sm" />
                  <div className="ml-auto flex items-center gap-1">
                    <MetricText
                      value={company.open_positions_count}
                      size="sm"
                      showTrendIcon={false}
                    />
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      open
                    </span>
                  </div>
                </div>

                {/* Tech stack */}
                <div className="flex flex-wrap gap-1.5">
                  {company.tech_stack.slice(0, 4).map((tech) => (
                    <SkillTag key={tech} name={tech} variant="default" />
                  ))}
                  {company.tech_stack.length > 4 && (
                    <span
                      className="inline-flex h-6 px-2 rounded-md text-[11px] items-center"
                      style={{
                        color: "var(--text-muted)",
                        background: "var(--surface-hover)",
                      }}
                    >
                      +{company.tech_stack.length - 4}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
