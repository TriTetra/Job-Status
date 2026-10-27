"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const headers = new Headers();
  if (typeof window !== "undefined") {
    const clerk = (window as any).Clerk;
    const token = await clerk?.session?.getToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { credentials: "include", headers });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<T>;
}

export interface BadgeCounts {
  /** APPLY bucket — Opportunities sidebar badge */
  opportunities: number | null;
  /** Active (non-rejected, non-offer) applications — Applications sidebar badge */
  applications: number | null;
}

export function useBadgeCounts(): BadgeCounts {
  const [counts, setCounts] = useState<BadgeCounts>({
    opportunities: null,
    applications: null,
  });

  useEffect(() => {
    // Opportunities: how many jobs are scored APPLY
    apiFetch<{ total: number; jobs: unknown[] }>(
      "/api/jobs/?recommendation=APPLY&limit=1"
    )
      .then((d) =>
        setCounts((prev) => ({ ...prev, opportunities: d.total }))
      )
      .catch(() => {});

    // Applications: sum of active pipeline buckets
    apiFetch<Record<string, number>>("/api/applications/summary")
      .then((summary) => {
        const active =
          (summary.applied ?? 0) +
          (summary.screening ?? 0) +
          (summary.interview ?? 0) +
          (summary.offer ?? 0);
        setCounts((prev) => ({ ...prev, applications: active }));
      })
      .catch(() => {});
  }, []);

  return counts;
}
