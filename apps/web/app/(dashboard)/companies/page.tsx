"use client";

import { useState } from "react";
import Link from "next/link";
import { NarrativeText } from "@/components/shared/narrative-text";
import { StatusPill } from "@/components/ui/status-pill";
import { MetricText } from "@/components/shared/metric-text";
import { SkillTag } from "@/components/ui/skill-tag";
import { Button } from "@/components/shared/button";
import { Search, Plus, Building2, MapPin, TrendingUp, TrendingDown, Minus } from "lucide-react";

type TierFilter = "ALL" | "Big Tech" | "Unicorn" | "Large" | "Startup";
type HiringDir = "spike" | "up" | "stable" | "down";

const MOCK_COMPANIES = [
  {
    slug: "stripe",
    name: "Stripe",
    tier: "Unicorn",
    industry: "Fintech",
    headquarters: "San Francisco, CA",
    openPositions: 12,
    hiringDirection: "up" as HiringDir,
    hiringDelta: 4,
    techStack: ["Ruby", "Go", "Rust", "Python", "Kafka"],
    applications: 2,
  },
  {
    slug: "anthropic",
    name: "Anthropic",
    tier: "Unicorn",
    industry: "AI Research",
    headquarters: "San Francisco, CA",
    openPositions: 8,
    hiringDirection: "spike" as HiringDir,
    hiringDelta: 6,
    techStack: ["Python", "PyTorch", "JAX", "Rust"],
    applications: 1,
  },
  {
    slug: "google",
    name: "Google",
    tier: "Big Tech",
    industry: "Search / Cloud / AI",
    headquarters: "Mountain View, CA",
    openPositions: 45,
    hiringDirection: "stable" as HiringDir,
    hiringDelta: 0,
    techStack: ["Python", "Go", "Java", "C++", "Kubernetes", "TensorFlow"],
    applications: 3,
  },
  {
    slug: "databricks",
    name: "Databricks",
    tier: "Unicorn",
    industry: "Data / AI Platform",
    headquarters: "San Francisco, CA",
    openPositions: 15,
    hiringDirection: "up" as HiringDir,
    hiringDelta: 2,
    techStack: ["Scala", "Python", "Java", "Spark", "Delta Lake"],
    applications: 0,
  },
  {
    slug: "linear",
    name: "Linear",
    tier: "Startup",
    industry: "Developer Tools",
    headquarters: "Remote",
    openPositions: 4,
    hiringDirection: "stable" as HiringDir,
    hiringDelta: 0,
    techStack: ["TypeScript", "React", "Node.js", "PostgreSQL"],
    applications: 0,
  },
  {
    slug: "vercel",
    name: "Vercel",
    tier: "Unicorn",
    industry: "Developer Platform",
    headquarters: "Remote",
    openPositions: 9,
    hiringDirection: "up" as HiringDir,
    hiringDelta: 3,
    techStack: ["TypeScript", "React", "Next.js", "Rust", "Go"],
    applications: 1,
  },
];

type TrendVariant = "success" | "warning" | "neutral";

const directionConfig: Record<
  HiringDir,
  { label: string; variant: TrendVariant; Icon: typeof TrendingUp }
> = {
  spike:  { label: "SPIKE",  variant: "success", Icon: TrendingUp },
  up:     { label: "UP",     variant: "success", Icon: TrendingUp },
  stable: { label: "STABLE", variant: "neutral", Icon: Minus },
  down:   { label: "DOWN",   variant: "warning", Icon: TrendingDown },
};

const iconBg: Record<TrendVariant, string> = {
  success: "rgba(127,182,133,0.12)",
  warning: "rgba(255,177,98,0.12)",
  neutral: "var(--surface-hover)",
};
const iconColor: Record<TrendVariant, string> = {
  success: "var(--success)",
  warning: "var(--warning)",
  neutral: "var(--text-muted)",
};

export default function CompaniesPage() {
  const [tierFilter, setTierFilter] = useState<TierFilter>("ALL");
  const [search, setSearch] = useState("");

  const filtered = MOCK_COMPANIES.filter((c) => {
    if (tierFilter !== "ALL" && c.tier !== tierFilter) return false;
    if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const hiringNow = MOCK_COMPANIES.filter(
    (c) => c.hiringDirection === "up" || c.hiringDirection === "spike"
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
            {MOCK_COMPANIES.length} tracked · {hiringNow} hiring now
          </p>
        </div>
        <Button variant="outline" size="md">
          <Plus className="h-4 w-4" />
          Track company
        </Button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center gap-3 flex-wrap">
        <div
          className="flex items-center gap-1 p-1 rounded-lg"
          style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
        >
          {(["ALL", "Big Tech", "Unicorn", "Large", "Startup"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTierFilter(t)}
              className="px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
              style={{
                background: tierFilter === t ? "rgba(255,177,98,0.15)" : "transparent",
                color: tierFilter === t ? "var(--accent)" : "var(--text-secondary)",
              }}
            >
              {t}
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((company) => {
          const direction = directionConfig[company.hiringDirection];
          const DirectionIcon = direction.Icon;

          return (
            <Link
              key={company.slug}
              href={`/companies/${company.slug}`}
              className="surface p-5 hover:bg-surface-hover transition-colors block"
              style={{ textDecoration: "none" }}
            >
              {/* Logo + name */}
              <div className="flex items-start gap-3 mb-3">
                <div
                  className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{ background: "rgba(255,177,98,0.12)" }}
                >
                  <span className="font-display font-semibold" style={{ color: "var(--accent)" }}>
                    {company.name.charAt(0)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <NarrativeText size="base" weight="semibold" className="truncate">
                    {company.name}
                  </NarrativeText>
                  <div className="mt-0.5">
                    <StatusPill label={company.tier} variant="neutral" size="sm" />
                  </div>
                </div>
              </div>

              {/* Meta */}
              <div className="space-y-1.5 mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
                <div className="flex items-center gap-1.5">
                  <Building2 className="h-3 w-3" strokeWidth={1.75} />
                  {company.industry}
                </div>
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-3 w-3" strokeWidth={1.75} />
                  {company.headquarters}
                </div>
              </div>

              {/* Hiring trend */}
              <div
                className="flex items-center gap-2 mb-3 pb-3 border-b"
                style={{ borderColor: "var(--border)" }}
              >
                <div
                  className="h-6 w-6 rounded flex items-center justify-center"
                  style={{ background: iconBg[direction.variant] }}
                >
                  <DirectionIcon
                    className="h-3.5 w-3.5"
                    strokeWidth={2}
                    style={{ color: iconColor[direction.variant] }}
                  />
                </div>
                <StatusPill label={direction.label} variant={direction.variant} size="sm" />
                <div className="ml-auto flex items-center gap-1">
                  <MetricText value={company.openPositions} size="sm" showTrendIcon={false} />
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>open</span>
                </div>
              </div>

              {/* Tech stack */}
              <div className="flex flex-wrap gap-1.5 mb-3">
                {company.techStack.slice(0, 4).map((tech) => (
                  <SkillTag key={tech} name={tech} variant="default" />
                ))}
                {company.techStack.length > 4 && (
                  <span
                    className="inline-flex h-6 px-2 rounded-md text-[11px] items-center"
                    style={{ color: "var(--text-muted)", background: "var(--surface-hover)" }}
                  >
                    +{company.techStack.length - 4}
                  </span>
                )}
              </div>

              {/* Applications */}
              {company.applications > 0 && (
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {company.applications} application{company.applications > 1 ? "s" : ""} tracked
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
