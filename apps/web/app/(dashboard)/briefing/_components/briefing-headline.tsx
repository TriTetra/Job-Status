"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowUpRight, Check, Minus, X } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { ScoreRing } from "@/components/ui/score-ring";
import { opportunitiesApi } from "@/features/opportunities/api";
import type { BriefingHeadline as Headline } from "@/features/briefing/types";

const REC_COLOR = { APPLY: "var(--success)", CONSIDER: "var(--accent)", SKIP: "var(--text-muted)" } as const;
const CHANCE_LABEL = { high: "good chance", medium: "fair chance", low: "long shot" } as const;

type Busy = null | "shortlist" | "skip";

/** The one job worth your attention today: who, why, the facts, and what to do with it. */
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
    <section>
      <p className="text-[11px] uppercase tracking-[0.08em]" style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>
        Top pick
      </p>
      <div className="mt-4 flex items-start gap-5">
        <CompanyLogo name={h.company} companyKey={h.companyKey} size={60} />
        <div className="min-w-0 flex-1">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{h.company}</p>
          <h2 className="font-serif-display text-[28px] xl:text-[32px] leading-tight" style={{ color: "var(--text-primary)" }}>{h.title}</h2>
          {h.meta && <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>{h.meta}</p>}
        </div>
        <div className="hidden sm:flex flex-col items-center gap-1">
          <ScoreRing score={h.score} color={REC_COLOR[h.recommendation]} size={64} />
          <span className="text-[11px] whitespace-nowrap" style={{ color: REC_COLOR[h.recommendation] }}>
            {h.recommendation === "APPLY" ? "apply" : "worth a look"}
          </span>
          <span className="text-[11px] whitespace-nowrap" style={{ color: "var(--text-muted)" }}>{CHANCE_LABEL[h.chance]}</span>
        </div>
      </div>

      <p className="font-editorial mt-5 text-lg xl:text-xl leading-relaxed line-clamp-3" style={{ color: "var(--text-secondary)" }}>
        {h.why}
      </p>

      {h.criteria.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm" aria-label="Against your priorities">
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

      <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-3 text-sm">
        {h.postingUrl && (
          <a href={h.postingUrl} target="_blank" rel="noopener noreferrer"
             className="inline-flex items-center gap-1.5 rounded-lg px-4 h-10 font-semibold" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
            Open posting <ArrowUpRight className="h-4 w-4" strokeWidth={2} />
          </a>
        )}
        <button onClick={() => decide("to_apply")} disabled={busy !== null || done === "shortlisted"}
                className="disabled:opacity-60" style={{ color: "var(--text-primary)" }}>
          {busy === "shortlist" ? "Saving…" : done === "shortlisted" ? "Shortlisted ✓" : "Shortlist"}
        </button>
        <button onClick={() => decide("skipped")} disabled={busy !== null} className="disabled:opacity-60" style={{ color: "var(--text-muted)" }}>
          {busy === "skip" ? "Skipping…" : "Not for me"}
        </button>
        <Link href={h.inboxHref} className="sm:ml-auto" style={{ color: "var(--text-muted)" }}>Read the posting →</Link>
      </div>
      {done === "error" && <p className="mt-2 text-sm" role="alert" style={{ color: "var(--danger)" }}>That didn&apos;t save. Try again.</p>}
    </section>
  );
}
