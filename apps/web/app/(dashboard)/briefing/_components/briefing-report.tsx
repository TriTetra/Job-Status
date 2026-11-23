"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { applyApi, type DailyReport } from "@/features/apply/api";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

const STATE_COLOR: Record<string, string> = {
  "probably ghosted": "var(--text-muted)",
  "closed (no answer)": "var(--text-muted)",
  "follow up": "var(--accent)",
  interviewing: "var(--success)",
  offer: "var(--success)",
};

/** Today's report: what's ready to send, where your applications stand and their chance now, what to learn. */
export function BriefingReport() {
  const [r, setR] = useState<DailyReport | null>(null);

  useEffect(() => {
    applyApi.report().then(setR).catch(() => {});
  }, []);

  if (!r || (!r.queue.length && !r.active.length && !r.learn.length)) return null;
  return (
    <section className="mb-7" aria-label="Today's report">
      <p className={LABEL} style={LABEL_STYLE}>Today</p>
      {r.queue.length > 0 && (
        <p className="mt-2.5 text-[15px]" style={{ color: "var(--text-primary)" }}>
          <span className="font-serif-display text-2xl tabular-nums mr-1.5">{r.queue.length}</span>
          ready to apply, prepared for you.{" "}
          <Link href="/apply" className="text-sm whitespace-nowrap" style={{ color: "var(--accent)" }}>Open the queue →</Link>
        </p>
      )}
      {r.active.length > 0 && (
        <div className="mt-3">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Waiting on {r.active.length}{r.ghosted ? `, ${r.ghosted} probably ghosted` : ""} · sent this week: {r.sent_this_week}
          </p>
          <ul className="mt-1.5 space-y-1">
            {r.active.slice(0, 4).map((a) => (
              <li key={a.url} className="text-xs flex flex-wrap gap-x-1.5" style={{ color: "var(--text-muted)" }}>
                <span style={{ color: "var(--text-secondary)" }}>{a.company}</span>
                <span style={{ color: STATE_COLOR[a.state] ?? "var(--text-muted)" }}>· {a.state}{a.days != null ? `, ${a.days} days` : ""}</span>
                {typeof a.chance_now === "number" && <span>· {(a.chance_now * 100).toFixed(1)}% chance of an answer now</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {r.learn.length > 0 && (
        <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
          Learn next: <span style={{ color: "var(--text-primary)" }}>{r.learn[0].skill}</span>
          <span style={{ color: "var(--text-muted)" }}> · missing in {r.learn[0].jobs} of your good matches</span>
        </p>
      )}
    </section>
  );
}
