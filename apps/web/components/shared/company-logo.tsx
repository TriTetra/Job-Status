"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CompanyLogoProps {
  name: string;
  /** Board key (infra/config/companies.yaml); without one the monogram shows */
  companyKey?: string | null;
  size?: number;
  className?: string;
}

function initials(name: string): string {
  const words = name.replace(/[^\p{L}\p{N} ]/gu, " ").split(/\s+/).filter(Boolean);
  return (words.length > 1 ? words[0][0] + words[1][0] : (words[0] ?? "?").slice(0, 2)).toUpperCase();
}

/**
 * The company's logo on a light tile (dark marks stay visible on the dark UI);
 * a monogram when there is no logo.
 */
export function CompanyLogo({ name, companyKey, size = 36, className }: CompanyLogoProps) {
  const [failed, setFailed] = useState(false);
  const radius = Math.round(size * 0.24);
  const box = { width: size, height: size, borderRadius: radius };

  if (!companyKey || failed) {
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
        src={`/api/companies/logo/${encodeURIComponent(companyKey)}`}
        alt=""
        width={Math.round(size * 0.7)}
        height={Math.round(size * 0.7)}
        loading="lazy"
        onError={() => setFailed(true)}
        style={{ width: "70%", height: "70%", objectFit: "contain" }}
      />
    </span>
  );
}
