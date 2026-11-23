import { ArrowUpRight } from "lucide-react";

const DACH = /germany|deutschland|austria|österreich|switzerland|schweiz|suisse|berlin|munich|münchen|hamburg|frankfurt|cologne|köln|stuttgart|düsseldorf|vienna|wien|zurich|zürich|geneva|genève|basel|lausanne/i;
const TURKEY = /turkey|türkiye|turkiye|istanbul|İstanbul|ankara|izmir|İzmir|bursa|antalya|kocaeli/i;

const google = (site: string, company: string) =>
  `https://www.google.com/search?q=${encodeURIComponent(`site:${site} "${company}"`)}`;

/** Where to read about an employer, for this company (and where it is). Links only: Aplio doesn't read these sites. */
export function reviewLinks(company: string, location = ""): { name: string; what: string; href: string }[] {
  const c = company.trim();
  if (!c) return [];
  const links = [
    { name: "Glassdoor", what: "reviews, salaries, interviews",
      href: `https://www.glassdoor.com/Search/results.htm?keyword=${encodeURIComponent(c)}` },
    { name: "Reddit", what: "threads from people who work there",
      href: `https://www.reddit.com/search/?q=${encodeURIComponent(`"${c}" (working OR interview OR culture)`)}` },
    { name: "Blind", what: "anonymous posts by verified employees", href: google("teamblind.com", c) },
  ];
  if (DACH.test(location)) links.splice(1, 0, { name: "kununu", what: "reviews from Germany, Austria and Switzerland", href: google("kununu.com", c) });
  if (TURKEY.test(location)) links.push({ name: "Ekşi Sözlük", what: "what people in Turkey write about it", href: google("eksisozluk.com", c) });
  return links;
}

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

/** "What people say": the review sites worth a look for this employer, opened on their own sites. */
export function WhatPeopleSay({ company, location }: { company: string; location?: string | null }) {
  const links = reviewLinks(company, location ?? "");
  if (!links.length) return null;
  return (
    <section>
      <p className={LABEL} style={LABEL_STYLE}>What people say</p>
      <ul className="mt-2 space-y-1.5">
        {links.map((l) => (
          <li key={l.name} className="text-xs leading-relaxed">
            <a href={l.href} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-0.5 font-medium hover:underline underline-offset-2"
               style={{ color: "var(--text-primary)" }}>
              {l.name} <ArrowUpRight className="h-3 w-3" strokeWidth={2} style={{ color: "var(--text-muted)" }} />
            </a>{" "}
            <span style={{ color: "var(--text-muted)" }}>{l.what}</span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px]" style={{ color: "var(--text-muted)" }}>Opens on their sites; Aplio doesn&apos;t collect reviews.</p>
    </section>
  );
}
