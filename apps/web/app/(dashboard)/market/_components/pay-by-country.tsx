"use client";

import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { countryName } from "@/components/ui/place-badge";
import type { PayByCountry, PayStats } from "@/features/market/types";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const SHOWN = 4;

function money(currency: string | null, n: number | undefined): string {
  if (n == null) return "—";
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency: currency ?? "USD", notation: "compact",
      maximumFractionDigits: 0 }).format(n);
  } catch {
    return String(n);
  }
}

function stat(currency: string | null, s: PayStats, min: number): string {
  if (s.median == null) return `${s.postings} posting${s.postings === 1 ? "" : "s"}, fewer than ${min} to say`;
  const range = s.p25 != null && s.p75 != null ? ` · ${money(currency, s.p25)}–${money(currency, s.p75)} middle half` : "";
  return `${money(currency, s.median)} median${range} · ${s.postings} postings`;
}

/** What tech roles pay where you look: stated pay from postings, and official figures with their source. */
export function PayByCountrySection({ pay }: { pay: PayByCountry }) {
  const [all, setAll] = useState(false);
  const countries = pay.countries.filter((c) => c.all.postings > 0 || c.official.length > 0);
  if (countries.length === 0) return null;
  const shown = all ? countries : countries.slice(0, SHOWN);

  return (
    <section className="shrink-0">
      <p className={LABEL} style={LABEL_STYLE}>What tech roles pay · yearly, as stated</p>
      <ul className="mt-3 space-y-4">
        {shown.map((c) => (
          <li key={c.code} className="text-sm">
            <p className="flex items-baseline gap-2" style={{ color: "var(--text-primary)" }}>
              <span className={`fi fi-${c.code.toLowerCase()} shrink-0 rounded-[2px]`} aria-hidden="true" />
              <span className="font-medium">{countryName(c.code)}</span>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {c.all.postings ? stat(c.currency, c.all, pay.min_postings) : "no postings state pay"}
              </span>
            </p>
            {c.families.filter((f) => f.median != null).slice(0, 4).map((f) => (
              <p key={f.family} className="mt-1 pl-6 grid grid-cols-[8.5rem_minmax(0,1fr)] gap-3 text-xs">
                <span style={{ color: "var(--text-secondary)" }}>{f.family}</span>
                <span className="tabular-nums" style={{ color: "var(--text-muted)" }}>
                  <span style={{ color: "var(--text-primary)" }}>{money(c.currency, f.median)}</span>
                  {f.p25 != null && f.p75 != null ? ` · ${money(c.currency, f.p25)}–${money(c.currency, f.p75)}` : ""} · {f.postings}
                </span>
              </p>
            ))}
            {c.official.map((o) => (
              <p key={o.url} className="mt-1 pl-6 text-xs" style={{ color: "var(--text-muted)" }}>
                Official: <span style={{ color: "var(--text-primary)" }}>{money(o.currency, o.median)}</span> median for{" "}
                {o.occupation.charAt(0).toLowerCase() + o.occupation.slice(1)}, {o.reference} ·{" "}
                <a href={o.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 underline underline-offset-2">
                  {o.source} <ArrowUpRight className="h-3 w-3" />
                </a>
              </p>
            ))}
          </li>
        ))}
      </ul>
      {countries.length > SHOWN && (
        <button onClick={() => setAll((v) => !v)} className="mt-3 text-xs underline underline-offset-4" style={{ color: "var(--text-muted)" }}>
          {all ? "Fewer countries" : `All ${countries.length} countries`}
        </button>
      )}
      <p className="mt-3 text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
        From postings seen in the last {pay.window_days} days that state a yearly salary for one country, in its
        currency (ranges count by their midpoint). Posted pay runs above what most people in a role earn: big
        and well-paying employers post it more often. Official figures cover everyone in the occupation.
      </p>
    </section>
  );
}
