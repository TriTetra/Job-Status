import { Building2, Globe2, Laptop, MapPin, Shuffle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { OpportunityExplanation } from "@/features/opportunities/types";

/**
 * Where a job is, at a glance: the country's flag, the city, and how you'd work there
 * (On-site · Hybrid · Remote · Global). Flags are SVGs from flag-icons, served by this site.
 */

const EUROPE_WORDS = /^(europe|eu|european union|eea)$/i;
const ANYWHERE = /anywhere|worldwide|global/i;

type Work = "onsite" | "hybrid" | "remote" | null;

const WORK: Record<Exclude<Work, null>, { label: string; icon: typeof Building2; color: string }> = {
  onsite: { label: "On-site", icon: Building2, color: "var(--text-secondary)" },
  hybrid: { label: "Hybrid", icon: Shuffle, color: "var(--accent)" },
  remote: { label: "Remote", icon: Laptop, color: "var(--success)" },
};

let regionNames: Intl.DisplayNames | null = null;
/** "TR" → "Türkiye" (the browser's own country names). */
export function countryName(code: string): string {
  try {
    regionNames ??= new Intl.DisplayNames(["en"], { type: "region" });
    return regionNames.of(code) ?? code;
  } catch {
    return code;
  }
}

function Flag({ code, title }: { code: string; title?: string }) {
  return (
    <span className={cn("fi", `fi-${code.toLowerCase()}`, "shrink-0 rounded-[2px] shadow-[0_0_0_1px_rgba(238,233,223,0.12)]")}
          style={{ width: "1.25em", height: "0.94em", backgroundSize: "cover" }}
          role="img" aria-label={title ?? code} title={title ?? code} />
  );
}

/** "Istanbul / Maslak" → "Istanbul"; "London, UK • Berlin, Germany" → "London" (+1 more place). */
export function cityOf(location: string | null | undefined): { city: string | null; more: number } {
  const raw = (location ?? "").replace(/^(remote|hybrid|on-?site)\s*[:\-–]\s*/i, "").trim();
  if (!raw || /^unknown$/i.test(raw)) return { city: null, more: 0 };
  const places = raw.split(/\s*(?:[•;|]|\bor\b|\band\b)\s*/i).filter(Boolean);
  const first = places[0].split(/\s*[,/(]\s*/)[0].trim();
  return { city: first || null, more: Math.max(0, places.length - 1) };
}

function workOf(ex: OpportunityExplanation): Work {
  if (ex.remote) return "remote";
  if (ex.workplace === "hybrid" || ex.workplace === "onsite") return ex.workplace;
  if (/\bhybrid\b/i.test(ex.location ?? "")) return "hybrid";
  return null;
}

export function PlaceBadge({ ex, className, compact = false }: {
  ex: OpportunityExplanation; className?: string; compact?: boolean;
}) {
  const work = workOf(ex);
  const codes = (ex.countries ?? []).filter((c) => /^[A-Z]{2}$/.test(c));
  const regions = (ex.remote_regions ?? []).filter(Boolean);
  const text = "text-xs";

  // Remote: where you may live, not where the office is
  if (work === "remote") {
    const global = ex.remote_scope === "worldwide" || regions.some((r) => ANYWHERE.test(r)) || ANYWHERE.test(ex.location ?? "");
    const europe = regions.find((r) => EUROPE_WORDS.test(r.trim()));
    const emea = regions.find((r) => /^emea$/i.test(r.trim()));
    let lead: React.ReactNode = <Globe2 className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--success)" }} aria-hidden />;
    let where = "Global";
    if (!global) {
      if (europe) { lead = <Flag code="eu" title="Europe" />; where = "Europe"; }
      else if (emea) { where = "EMEA"; }
      else if (codes.length) {
        lead = <span className="inline-flex gap-1">{codes.slice(0, 3).map((c) => <Flag key={c} code={c} title={countryName(c)} />)}</span>;
        where = codes.length === 1 ? countryName(codes[0])
          : codes.length > 3 ? `${codes.slice(0, 3).join(", ")} +${codes.length - 3}` : codes.join(", ");
      } else if (regions.length) {
        where = regions.length > 2 ? `${regions.slice(0, 2).join(", ")} +${regions.length - 2}` : regions.join(", ");
      } else {
        where = "location not stated";
      }
    }
    return (
      <span className={cn("inline-flex items-center gap-1.5 min-w-0", text, className)}>
        {lead}
        <span className="truncate" style={{ color: "var(--text-secondary)" }}>
          <span style={{ color: WORK.remote.color }}>Remote</span>{!compact || where !== "Global" ? ` · ${where}` : " · Global"}
        </span>
      </span>
    );
  }

  const { city, more } = cityOf(ex.location);
  const w = work ? WORK[work] : null;
  return (
    <span className={cn("inline-flex items-center gap-1.5 min-w-0", text, className)}>
      {codes.length ? <Flag code={codes[0]} title={countryName(codes[0])} /> : <MapPin className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--text-muted)" }} aria-hidden />}
      <span className="truncate" style={{ color: "var(--text-secondary)" }}>
        {city ?? (codes[0] ? countryName(codes[0]) : "Location not stated")}
        {more > 0 && <span style={{ color: "var(--text-muted)" }}> +{more}</span>}
      </span>
      {w && (
        <span className="inline-flex items-center gap-0.5 shrink-0" style={{ color: w.color }}>
          <w.icon className="h-3 w-3" aria-hidden />{w.label}
        </span>
      )}
    </span>
  );
}
