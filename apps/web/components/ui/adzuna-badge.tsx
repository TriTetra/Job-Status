import { cn } from "@/lib/utils";

/**
 * Adzuna's terms: every displayed Adzuna listing is labelled "Adzuna", at least 116×23 px,
 * linked to Adzuna's site for that country (developer.adzuna.com/docs/terms_of_service).
 */
const SITES: Record<string, string> = {
  GB: "https://www.adzuna.co.uk", DE: "https://www.adzuna.de", NL: "https://www.adzuna.nl", PL: "https://www.adzuna.pl",
  AT: "https://www.adzuna.at", ES: "https://www.adzuna.es", CH: "https://www.adzuna.ch", FR: "https://www.adzuna.fr",
  IT: "https://www.adzuna.it", BE: "https://www.adzuna.be", US: "https://www.adzuna.com", CA: "https://www.adzuna.ca",
  AU: "https://www.adzuna.com.au", NZ: "https://www.adzuna.co.nz", SG: "https://www.adzuna.sg", IN: "https://www.adzuna.in",
};

export const isAdzuna = (source: unknown) => source === "adzuna";

export function AdzunaBadge({ country, className }: { country?: string | null; className?: string }) {
  const href = SITES[(country ?? "").toUpperCase()] ?? SITES.GB;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" title="Job from Adzuna"
       className={cn("inline-flex items-center justify-center rounded-md border text-xs font-semibold tracking-wide hover:bg-[var(--surface-hover)]", className)}
       style={{ minWidth: 116, height: 23, borderColor: "var(--border-strong)", color: "var(--text-secondary)" }}>
      Jobs by Adzuna
    </a>
  );
}
