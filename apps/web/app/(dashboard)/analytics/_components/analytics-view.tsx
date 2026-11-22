import Link from "next/link";
import type { ApplicationAnalytics } from "@/features/applications/api";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;
const pct = (x: number | null | undefined) => (x == null ? "—" : `${Math.round(x * 100)}%`);
const STAGE_LABEL = { tracked: "Tracked", applied: "Applied", interview: "Interview", offer: "Offer" } as const;

function lead(a: ApplicationAnalytics): string {
  const applied = a.funnel.find((f) => f.stage === "applied")?.count ?? 0;
  const interviews = a.funnel.find((f) => f.stage === "interview")?.count ?? 0;
  if (!applied) return "No applications sent yet. Once you mark roles as applied, this page shows what's working.";
  const parts = [`You've applied to ${applied} role${applied === 1 ? "" : "s"}; ${interviews} led to an interview (${pct(a.interview_rate)}).`];
  if (a.response.sent) parts.push(`Of those sent two weeks ago or more, ${pct(a.response.rate)} heard back.`);
  return parts.join(" ");
}

/** The one thing the numbers suggest doing, if they suggest anything yet. */
function insight(a: ApplicationAnalytics): { text: string; href?: string; cta?: string } | null {
  const [hi, , lo] = a.by_score;
  const rate = (b: { applied: number; interviews: number }) => (b.applied ? b.interviews / b.applied : 0);
  if (a.waiting.stale) {
    return { text: `${a.waiting.stale} application${a.waiting.stale === 1 ? " has" : "s have"} waited two weeks or more without an answer. A short follow-up often gets one.`, href: "/applications", cta: "See them" };
  }
  if (hi && lo && hi.applied >= 3 && lo.applied >= 3 && rate(hi) > rate(lo) * 1.5) {
    return { text: `Your 70+ matches turn into interviews ${pct(rate(hi))} of the time, against ${pct(rate(lo))} under 55. Spend your applications there.`, href: "/inbox", cta: "Strong matches" };
  }
  if (a.applied_this_week === 0 && a.open_matches > 0) {
    return { text: `Nothing sent this week, and ${a.open_matches} open roles fit you.`, href: "/inbox", cta: "Pick one" };
  }
  return null;
}

/** Your search in numbers: the funnel, the pace, who answers, and whether your score predicts it. */
export function AnalyticsView({ a }: { a: ApplicationAnalytics }) {
  const funnel = [{ stage: "matches", label: "Open matches", count: a.open_matches }, ...a.funnel.map((f) => ({ ...f, label: STAGE_LABEL[f.stage] }))];
  const top = Math.max(1, ...funnel.map((f) => f.count));
  const weekMax = Math.max(1, ...a.weekly_applied);
  const tip = insight(a);
  const numbers = [
    { value: String(a.applied_this_week), label: "applied this week" },
    { value: pct(a.interview_rate), label: "of applications reach an interview" },
    { value: pct(a.response.rate), label: "heard back (sent 2+ weeks ago)", note: a.response.sent ? `${a.response.answered} of ${a.response.sent}` : "too early to tell" },
    { value: a.waiting.median_days != null ? `${a.waiting.median_days}d` : "—", label: "typical wait right now", note: a.waiting.count ? `${a.waiting.count} waiting` : "none waiting" },
  ];

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5">
      <header className="shrink-0 grid 2xl:grid-cols-[minmax(0,1fr)_minmax(0,720px)] gap-x-12 gap-y-6 items-end pb-6 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-[760px]">
          <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Analytics</h1>
          <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>{lead(a)}</p>
        </div>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-10 gap-y-5">
          {numbers.map((n) => (
            <div key={n.label} className="min-w-0">
              <dd className="font-serif-display text-[34px] leading-none tabular-nums" style={{ color: "var(--text-primary)" }}>{n.value}</dd>
              <dt className="mt-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>{n.label}</dt>
              {n.note && <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>{n.note}</p>}
            </div>
          ))}
        </dl>
      </header>

      <div className="mt-6 lg:flex-1 lg:min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] gap-x-14 gap-y-10">
        {/* From match to offer */}
        <section className="min-w-0">
          <p className={LABEL} style={LABEL_STYLE}>From match to offer</p>
          <ol className="mt-5 space-y-4">
            {funnel.map((f, i) => {
              const prev = i > 0 ? funnel[i - 1].count : null;
              const step = prev ? f.count / prev : null;
              return (
                <li key={f.stage} className="grid grid-cols-[7rem_minmax(0,1fr)_3rem] sm:grid-cols-[8rem_minmax(0,1fr)_3.5rem_4.5rem] items-center gap-x-4">
                  <span className="text-sm" style={{ color: i === 0 ? "var(--text-secondary)" : "var(--text-primary)" }}>{f.label}</span>
                  <span className="h-7 rounded-md relative" style={{ background: "rgba(238,233,223,0.05)" }}>
                    <span className="absolute inset-y-0 left-0 rounded-md transition-all"
                          style={{ width: `${Math.max(f.count ? 2 : 0, (f.count / top) * 100)}%`, background: i === 0 ? "rgba(238,233,223,0.16)" : `rgba(255,177,98,${0.35 + i * 0.15})` }} />
                  </span>
                  <span className="font-serif-display text-xl tabular-nums text-right" style={{ color: "var(--text-primary)" }}>{f.count}</span>
                  <span className="hidden sm:block text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>
                    {step != null && i > 1 ? `→ ${pct(step)}` : ""}
                  </span>
                </li>
              );
            })}
          </ol>
          <p className="mt-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
            Arrows: share that made it from the stage above. A rejection after an interview still counts as an interview.
            {a.passed_on ? ` You passed on ${a.passed_on} role${a.passed_on === 1 ? "" : "s"}.` : ""}
          </p>

          {tip && (
            <div className="mt-8 pl-4 border-l-2" style={{ borderColor: "var(--accent)" }}>
              <p className="text-[15px] leading-relaxed" style={{ color: "var(--text-primary)" }}>{tip.text}</p>
              {tip.href && <Link href={tip.href} className="mt-1 inline-block text-sm" style={{ color: "var(--accent)" }}>{tip.cta} →</Link>}
            </div>
          )}
        </section>

        <div className="min-w-0 flex flex-col gap-10">
          {/* Pace */}
          <section>
            <div className="flex items-baseline justify-between">
              <p className={LABEL} style={LABEL_STYLE}>Applications per week</p>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>last 8 weeks</span>
            </div>
            <div className="mt-4 flex items-end gap-2 h-28" role="img" aria-label={`Applications per week: ${a.weekly_applied.join(", ")}`}>
              {a.weekly_applied.map((n, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1 h-full">
                  {n > 0 && <span className="text-[10px] tabular-nums" style={{ color: "var(--text-muted)" }}>{n}</span>}
                  <div className="w-full rounded-sm" style={{ height: n ? `${Math.max(8, (n / weekMax) * 85)}%` : "2px",
                    background: i === a.weekly_applied.length - 1 ? "var(--accent)" : "rgba(238,233,223,0.2)" }} />
                </div>
              ))}
            </div>
            <div className="mt-1.5 flex justify-between text-[10px]" style={{ color: "var(--text-muted)" }}>
              <span>8 weeks ago</span><span>this week</span>
            </div>
          </section>

          {/* Score vs outcome */}
          <section>
            <p className={LABEL} style={LABEL_STYLE}>Does your score predict interviews?</p>
            <table className="mt-4 w-full text-sm">
              <thead>
                <tr className="text-xs" style={{ color: "var(--text-muted)" }}>
                  <th className="text-left font-normal pb-2">Your fit</th>
                  <th className="text-right font-normal pb-2">Applied</th>
                  <th className="text-right font-normal pb-2">Interviews</th>
                  <th className="pb-2 w-[38%]" />
                </tr>
              </thead>
              <tbody>
                {a.by_score.map((b) => {
                  const r = b.applied ? b.interviews / b.applied : null;
                  return (
                    <tr key={b.band} className="border-t" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2.5" style={{ color: "var(--text-primary)" }}>{b.band}</td>
                      <td className="py-2.5 text-right font-mono text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>{b.applied}</td>
                      <td className="py-2.5 text-right font-mono text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>{b.interviews}</td>
                      <td className="py-2.5 pl-4">
                        <span className="flex items-center gap-2">
                          <span className="flex-1 h-1.5 rounded-full" style={{ background: "rgba(238,233,223,0.08)" }}>
                            <span className="block h-full rounded-full" style={{ width: `${(r ?? 0) * 100}%`, background: "var(--success)" }} />
                          </span>
                          <span className="w-9 text-right text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>{pct(r)}</span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-[11px]" style={{ color: "var(--text-muted)" }}>
              Only applications to roles Aplio scored. Few applications per band means the rate can swing.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
