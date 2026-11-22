"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowUpRight, Check, Minus, X } from "lucide-react";
import { SectionLabel } from "@/components/shared/narrative-section";
import { opportunitiesApi } from "@/features/opportunities/api";
import type { BriefingHeadline as Headline } from "@/features/briefing/types";
import { Movement } from "./movement";

const REC_COLOR = { APPLY: "var(--success)", CONSIDER: "var(--accent)", SKIP: "var(--text-muted)" } as const;
const CHANCE_LABEL = { high: "good chance", medium: "fair chance", low: "long shot" } as const;

type Busy = null | "shortlist" | "skip";

/** The one job worth your attention today: why, the facts, and what to do with it. */
export function BriefingHeadline({ h }: { h: Headline }) {
  const router = useRouter();
  const [busy, setBusy] = useState<Busy>(null);
  const [done, setDone] = useState<null | "shortlisted" | "error">(null);

  const decide = async (status: "to_apply" | "skipped") => {
    setBusy(status === "to_apply" ? "shortlist" : "skip");
    try {
      await opportunitiesApi.decide(h.url, status);
      if (status === "skipped") router.refresh(); // the next best match takes its place
      else setDone("shortlisted");
    } catch {
      setDone("error");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Movement delay={120}>
      <SectionLabel>Top pick</SectionLabel>
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="font-serif-display text-3xl md:text-4xl" style={{ color: "var(--text-primary)" }}>
          {h.company}
        </h2>
        <span className="font-mono text-lg font-semibold tabular-nums" style={{ color: REC_COLOR[h.recommendation] }}>
          {h.score}
        </span>
        <span className="text-[11px] uppercase tracking-wider" style={{ color: REC_COLOR[h.recommendation] }}>
          {h.recommendation === "APPLY" ? "apply" : "worth a look"} · {CHANCE_LABEL[h.chance]}
        </span>
      </div>
      <p className="mt-1 text-lg" style={{ color: "var(--text-primary)" }}>{h.title}</p>
      {h.meta && <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>{h.meta}</p>}

      <p className="font-editorial mt-6 text-xl leading-relaxed max-w-[680px]" style={{ color: "var(--text-secondary)" }}>
        {h.why}
      </p>

      {h.criteria.length > 0 && (
        <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-1 text-sm" aria-label="Against your priorities">
          {h.criteria.map((c) => (
            <li key={c.label} className="inline-flex items-center gap-1.5" style={{ color: "var(--text-secondary)" }}>
              {c.state === "confirmed" ? (
                <Check className="h-3.5 w-3.5" strokeWidth={2.5} style={{ color: "var(--success)" }} aria-label="matches" />
              ) : c.state === "conflict" ? (
                <X className="h-3.5 w-3.5" strokeWidth={2.5} style={{ color: "var(--danger)" }} aria-label="conflicts" />
              ) : (
                <Minus className="h-3.5 w-3.5" strokeWidth={2} style={{ color: "var(--text-muted)" }} aria-label="unknown" />
              )}
              {c.label}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
        {h.postingUrl && (
          <a href={h.postingUrl} target="_blank" rel="noopener noreferrer"
             className="inline-flex items-center gap-1 font-medium" style={{ color: "var(--accent)" }}>
            Open posting <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2} />
          </a>
        )}
        <button onClick={() => decide("to_apply")} disabled={busy !== null || done === "shortlisted"}
                className="transition-colors disabled:opacity-60" style={{ color: "var(--text-secondary)" }}>
          {busy === "shortlist" ? "Saving…" : done === "shortlisted" ? "Shortlisted ✓" : "Shortlist"}
        </button>
        <button onClick={() => decide("skipped")} disabled={busy !== null}
                className="transition-colors disabled:opacity-60" style={{ color: "var(--text-muted)" }}>
          {busy === "skip" ? "Skipping…" : "Not for me"}
        </button>
        <Link href={h.inboxHref} className="sm:ml-auto" style={{ color: "var(--text-muted)" }}>
          Why {h.score}? →
        </Link>
      </div>
      {done === "error" && (
        <p className="mt-3 text-sm" role="alert" style={{ color: "var(--danger)" }}>That didn&apos;t save. Try again.</p>
      )}
    </Movement>
  );
}
