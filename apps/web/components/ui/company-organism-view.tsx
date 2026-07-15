"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { MetricText } from "@/components/shared/metric-text";
import { LabelText } from "@/components/shared/label-text";
import { StatusPill } from "./status-pill";
import { SkillTag } from "./skill-tag";
import { Button } from "@/components/shared/button";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  MapPin,
  Users,
  Calendar,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export type HiringDirection = "spike" | "up" | "stable" | "down" | "freeze";

export interface CompanyOrganismProps {
  company: {
    name: string;
    logo?: string;
    tier: string;
    industry?: string;
    headquarters?: string;
    employeeCount?: number;
    founded?: number;
  };
  hiringTrend: {
    direction: HiringDirection;
    newPositionsThisWeek: number;
    delta: number;
  };
  techStack: string[];
  visa: {
    h1b?: boolean;
    euBlueCard?: boolean;
    other?: string[];
  };
  engineeringCulture?: string[];
  yourHistory?: {
    applications: number;
    lastOutcome?: string;
    topicsAsked?: string[];
    advice?: string;
    events?: { date: string; title: string; subtitle?: string }[];
  };
  onApply?: () => void;
  onViewOpenRoles?: () => void;
  onAddNote?: () => void;
  className?: string;
}

type TrendVariant = "success" | "warning" | "danger" | "neutral";

const directionConfig: Record<
  HiringDirection,
  { label: string; variant: TrendVariant; Icon: typeof TrendingUp }
> = {
  spike:  { label: "SPIKE",  variant: "success", Icon: TrendingUp },
  up:     { label: "UP",     variant: "success", Icon: TrendingUp },
  stable: { label: "STABLE", variant: "neutral", Icon: Minus },
  down:   { label: "DOWN",   variant: "warning", Icon: TrendingDown },
  freeze: { label: "FREEZE", variant: "danger",  Icon: XCircle },
};

const trendBg: Record<TrendVariant, string> = {
  success: "rgba(127,182,133,0.12)",
  warning: "rgba(255,177,98,0.12)",
  danger:  "rgba(201,106,90,0.12)",
  neutral: "var(--surface-hover)",
};
const trendColor: Record<TrendVariant, string> = {
  success: "var(--success)",
  warning: "var(--warning)",
  danger:  "var(--danger)",
  neutral: "var(--text-muted)",
};

function Section({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("pt-6 border-t", className)} style={{ borderColor: "var(--border)" }}>
      <LabelText className="mb-3 block">{label}</LabelText>
      {children}
    </div>
  );
}

export function CompanyOrganismView({
  company,
  hiringTrend,
  techStack,
  visa,
  engineeringCulture,
  yourHistory,
  onApply,
  onViewOpenRoles,
  onAddNote,
  className,
}: CompanyOrganismProps) {
  const trend = directionConfig[hiringTrend.direction];
  const TrendIcon = trend.Icon;

  const logoContent = company.logo ? (
    <img src={company.logo} alt={company.name} className="h-12 w-12 rounded-lg object-cover" />
  ) : (
    <div
      className="h-12 w-12 rounded-lg flex items-center justify-center shrink-0"
      style={{ background: "rgba(255,177,98,0.12)" }}
    >
      <span className="font-display text-lg font-semibold" style={{ color: "var(--accent)" }}>
        {company.name.charAt(0)}
      </span>
    </div>
  );

  return (
    <article className={cn("surface p-8", className)}>
      {/* Header */}
      <div className="flex items-start gap-4 mb-6 pb-6 border-b" style={{ borderColor: "var(--border)" }}>
        {logoContent}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <NarrativeText size="2xl" weight="semibold">{company.name}</NarrativeText>
            <StatusPill label={company.tier} variant="neutral" size="md" />
          </div>
          <div className="flex items-center gap-3 text-sm flex-wrap" style={{ color: "var(--text-muted)" }}>
            {company.industry && (
              <span className="inline-flex items-center gap-1">
                <Building2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                {company.industry}
              </span>
            )}
            {company.headquarters && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" strokeWidth={1.75} />
                {company.headquarters}
              </span>
            )}
            {company.employeeCount && (
              <span className="inline-flex items-center gap-1">
                <Users className="h-3.5 w-3.5" strokeWidth={1.75} />
                {company.employeeCount.toLocaleString()} employees
              </span>
            )}
            {company.founded && (
              <span className="inline-flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" strokeWidth={1.75} />
                Founded {company.founded}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Hiring Trend */}
      <Section label="Hiring Trend">
        <div className="flex items-center gap-3">
          <div
            className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: trendBg[trend.variant] }}
          >
            <TrendIcon
              className="h-[18px] w-[18px]"
              strokeWidth={1.75}
              style={{ color: trendColor[trend.variant] }}
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <StatusPill label={trend.label} variant={trend.variant} dot />
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {hiringTrend.newPositionsThisWeek} new positions this week
              </span>
            </div>
            {hiringTrend.delta !== 0 && (
              <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {hiringTrend.delta > 0 ? "+" : ""}{hiringTrend.delta} vs last week
              </div>
            )}
          </div>
        </div>
        {onViewOpenRoles && (
          <button
            onClick={onViewOpenRoles}
            className="mt-3 text-xs transition-colors"
            style={{ color: "var(--accent)" }}
          >
            View open positions →
          </button>
        )}
      </Section>

      {/* Engineering Culture */}
      {engineeringCulture && engineeringCulture.length > 0 && (
        <Section label="Engineering Culture">
          <div className="flex flex-wrap gap-2">
            {engineeringCulture.map((trait) => (
              <span
                key={trait}
                className="inline-flex h-7 px-3 rounded-md text-xs border"
                style={{
                  color: "var(--text-secondary)",
                  background: "var(--surface-hover)",
                  borderColor: "var(--border)",
                }}
              >
                {trait}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Tech Stack */}
      {techStack.length > 0 && (
        <Section label="Tech Stack">
          <div className="flex flex-wrap gap-2">
            {techStack.map((tech) => (
              <SkillTag key={tech} name={tech} variant="default" />
            ))}
          </div>
        </Section>
      )}

      {/* Visa */}
      <Section label="Visa Sponsorship">
        <div className="space-y-2">
          {visa.h1b !== undefined && (
            <div className="flex items-center gap-2 text-sm">
              {visa.h1b
                ? <CheckCircle2 className="h-4 w-4" strokeWidth={2} style={{ color: "var(--success)" }} />
                : <XCircle className="h-4 w-4" strokeWidth={1.5} style={{ color: "var(--text-muted)" }} />
              }
              <span style={{ color: visa.h1b ? "var(--text-primary)" : "var(--text-muted)" }}>
                H1B sponsorship (US)
              </span>
            </div>
          )}
          {visa.euBlueCard !== undefined && (
            <div className="flex items-center gap-2 text-sm">
              {visa.euBlueCard
                ? <CheckCircle2 className="h-4 w-4" strokeWidth={2} style={{ color: "var(--success)" }} />
                : <XCircle className="h-4 w-4" strokeWidth={1.5} style={{ color: "var(--text-muted)" }} />
              }
              <span style={{ color: visa.euBlueCard ? "var(--text-primary)" : "var(--text-muted)" }}>
                EU Blue Card
              </span>
            </div>
          )}
          {visa.other?.map((v) => (
            <div key={v} className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4" strokeWidth={2} style={{ color: "var(--success)" }} />
              <span style={{ color: "var(--text-primary)" }}>{v}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Your History */}
      {yourHistory && (
        <Section label="Your History">
          <div className="space-y-3 mb-4">
            <div className="flex items-center justify-between text-sm">
              <span style={{ color: "var(--text-secondary)" }}>Applications</span>
              <MetricText value={yourHistory.applications} size="sm" showTrendIcon={false} />
            </div>
            {yourHistory.lastOutcome && (
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: "var(--text-secondary)" }}>Last outcome</span>
                <span style={{ color: "var(--text-primary)" }}>{yourHistory.lastOutcome}</span>
              </div>
            )}
          </div>

          {yourHistory.topicsAsked && yourHistory.topicsAsked.length > 0 && (
            <div className="mb-4">
              <LabelText className="mb-1.5 block">Topics asked</LabelText>
              <div className="flex flex-wrap gap-1.5">
                {yourHistory.topicsAsked.map((topic) => (
                  <SkillTag key={topic} name={topic} variant="emphasized" />
                ))}
              </div>
            </div>
          )}

          {yourHistory.advice && (
            <div
              className="p-4 rounded-lg mb-4"
              style={{ background: "var(--surface-elevated)", border: "1px solid var(--border)" }}
            >
              <LabelText accent className="mb-1.5 block">Advice</LabelText>
              <NarrativeText size="sm">{yourHistory.advice}</NarrativeText>
            </div>
          )}

          {yourHistory.events && yourHistory.events.length > 0 && (
            <div className="space-y-0">
              {yourHistory.events.map((event, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="h-2 w-2 rounded-full mt-1.5 shrink-0" style={{ background: "var(--accent)" }} />
                    {i < yourHistory.events!.length - 1 && (
                      <div className="w-px flex-1 my-1" style={{ background: "var(--border)" }} />
                    )}
                  </div>
                  <div className="pb-4">
                    <div
                      className="text-[11px] font-medium uppercase tracking-wider mb-0.5"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {event.date}
                    </div>
                    <div className="text-sm" style={{ color: "var(--text-primary)" }}>{event.title}</div>
                    {event.subtitle && (
                      <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        └ {event.subtitle}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-6 border-t mt-6" style={{ borderColor: "var(--border)" }}>
        {onApply && <Button variant="primary" onClick={onApply}>Apply</Button>}
        {onViewOpenRoles && <Button variant="outline" onClick={onViewOpenRoles}>View open roles</Button>}
        {onAddNote && <Button variant="ghost" onClick={onAddNote}>Add note</Button>}
      </div>
    </article>
  );
}
