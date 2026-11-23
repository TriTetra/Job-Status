import Link from "next/link";
import { getBriefing } from "@/features/briefing/api";
import { BriefingHeadline } from "./_components/briefing-headline";
import { BriefingTodos } from "./_components/briefing-todos";
import { BriefingReport } from "./_components/briefing-report";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

/**
 * The daily briefing on one screen: who you are today and the week in numbers,
 * the one job worth your attention with what changed, and what to do next.
 */
export default async function BriefingPage() {
  const b = await getBriefing();
  // The lead already says how many new matches; the strip carries the rest (busy companies, closed jobs)
  const newMatches = b.changes.find((l) => l.linkLabel === "See them");
  const strip = b.changes.filter((l) => l !== newMatches && !l.text.startsWith("Nothing new"));
  return (
    <div className="lg:h-full w-full max-w-[1360px] mx-auto px-6 lg:px-12 py-8 lg:py-7 flex flex-col">
      {/* Masthead */}
        <header className="grid lg:grid-cols-[minmax(0,1fr)_auto] items-end gap-x-12 gap-y-6 shrink-0">
          <div className="min-w-0">
            <p className={LABEL} style={LABEL_STYLE}>{b.dateline}</p>
            <h1 className="mt-2.5 font-serif-display text-4xl xl:text-5xl leading-[1.05]" style={{ color: "var(--text-primary)" }}>
              {b.greeting}
            </h1>
            <p className="mt-3 text-lg leading-relaxed max-w-[680px]" style={{ color: "var(--text-secondary)" }}>
              {b.lead}
              {newMatches && (
                <Link href="/inbox" className="ml-2 text-sm whitespace-nowrap" style={{ color: "var(--accent)" }}>See them →</Link>
              )}
            </p>
            {strip.length > 0 && (
              <p className="mt-2 text-sm flex flex-wrap gap-x-4 gap-y-1" style={{ color: "var(--text-muted)" }}>
                {strip.slice(0, 3).map((l) =>
                  l.href ? (
                    <Link key={l.text} href={l.href} className="hover:underline underline-offset-4">{l.text}</Link>
                  ) : (
                    <span key={l.text}>{l.text}</span>
                  ),
                )}
              </p>
            )}
          </div>
          {b.week.length > 0 && (
            <dl className="grid grid-cols-3 gap-x-8 xl:gap-x-10" aria-label="This week">
              {b.week.map((n) => (
                <div key={n.label} className="min-w-[6.5rem]">
                  <dd className="font-serif-display text-[40px] leading-none tabular-nums" style={{ color: "var(--text-primary)" }}>{n.value}</dd>
                  <dt className="mt-2 text-xs leading-snug max-w-[9rem]" style={{ color: "var(--text-secondary)" }}>{n.label}</dt>
                  {n.note && <p className="mt-0.5 text-[11px]" style={{ color: "var(--text-muted)" }}>{n.note}</p>}
                </div>
              ))}
            </dl>
          )}
        </header>

      {/* Body: the pick + changes | to do */}
      <div className="mt-6 pt-6 border-t lg:flex-1 lg:min-h-0 grid lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-x-14 gap-y-10"
           style={{ borderColor: "var(--border)" }}>
        <div className="lg:min-h-0 lg:overflow-y-auto custom-scrollbar flex flex-col -mr-3 pr-3">
          {b.headline ? (
            <BriefingHeadline h={b.headline} />
          ) : (
            <div>
              <p className={LABEL} style={LABEL_STYLE}>Top pick</p>
              <p className="mt-4 font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>No strong match yet.</p>
              <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>Once your roles are scanned, the best one to apply to shows here.</p>
            </div>
          )}

        </div>

        <div className="lg:min-h-0 flex flex-col">
          <BriefingReport />
          <BriefingTodos todos={b.todos} />
        </div>
      </div>

      {/* Closing */}
      <footer className="mt-8 lg:mt-5 pt-4 border-t flex flex-wrap items-baseline justify-between gap-3 shrink-0" style={{ borderColor: "var(--border)" }}>
        <p className="font-editorial text-lg" style={{ color: "var(--text-secondary)" }}>{b.closing.join(" ")}</p>
        <Link href="/inbox" className="text-sm" style={{ color: "var(--text-muted)" }}>All opportunities →</Link>
      </footer>
    </div>
  );
}
