"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CompanyLogoProps {
  name: string;
  /** Board key (companies.yaml or a discovered board) */
  companyKey?: string | null;
  /** A stored job's URL: finds the logo of small companies too (website icon or the feed's logo) */
  jobUrl?: string | null;
  /** An employers-directory company's website domain */
  domain?: string | null;
  size?: number;
  className?: string;
}

function initials(name: string): string {
  const words = name.replace(/[^\p{L}\p{N} ]/gu, " ").split(/\s+/).filter(Boolean);
  return (words.length > 1 ? words[0][0] + words[1][0] : (words[0] ?? "?").slice(0, 2)).toUpperCase();
}

/**
 * The company's logo on a light tile (dark marks stay visible on the dark UI). Tries the
 * board logo, then the job's company logo, then shows a monogram.
 */
export function CompanyLogo({ name, companyKey, jobUrl, domain, size = 36, className }: CompanyLogoProps) {
  const sources = [
    companyKey ? `/api/companies/logo/${encodeURIComponent(companyKey)}` : null,
    jobUrl ? `/api/companies/logo-job?url=${encodeURIComponent(jobUrl)}` : null,
    domain ? `/api/companies/logo-domain?domain=${encodeURIComponent(domain)}` : null,
  ].filter((s): s is string => Boolean(s));
  const [attempt, setAttempt] = useState(0);
  const radius = Math.round(size * 0.24);
  const box = { width: size, height: size, borderRadius: radius };
  const src = sources[attempt];

  if (!src) {
    return (
      <span
        aria-hidden="true"
        className={cn("inline-flex shrink-0 items-center justify-center font-semibold", className)}
        style={{ ...box, background: "rgba(255,177,98,0.12)", color: "var(--accent)", fontSize: Math.round(size * 0.36) }}
      >
        {initials(name)}
      </span>
    );
  }
  return (
    <span className={cn("inline-flex shrink-0 items-center justify-center overflow-hidden", className)}
          style={{ ...box, background: "#F6F3EC" }}>
      {/* eslint-disable-next-line @next/next/no-img-element -- small same-origin icon, no optimisation needed */}
      <img
        key={src}
        src={src}
        alt=""
        width={Math.round(size * 0.7)}
        height={Math.round(size * 0.7)}
        loading="lazy"
        onError={() => setAttempt((a) => a + 1)}
        style={{ width: "70%", height: "70%", objectFit: "contain" }}
      />
    </span>
  );
}
