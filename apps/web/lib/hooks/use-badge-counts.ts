"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { ACTIVE_STATUSES } from "@/features/applications/api";

export interface BadgeCounts {
  /** APPLY bucket — Opportunities sidebar badge */
  opportunities: number | null;
  /** Applications still on the board (not rejected / withdrawn) — Applications sidebar badge */
  applications: number | null;
}

export function useBadgeCounts(): BadgeCounts {
  const [counts, setCounts] = useState<BadgeCounts>({
    opportunities: null,
    applications: null,
  });

  useEffect(() => {
    // Opportunities: how many jobs are scored APPLY (`total` counts all, limit=1 keeps the payload tiny)
    apiFetch<{ total: number; jobs: unknown[] }>("/api/jobs/?recommendation=APPLY&limit=1")
      .then((d) => setCounts((prev) => ({ ...prev, opportunities: d.total })))
      .catch((err) => console.warn("[badges] opportunities count failed:", err));

    // Applications: everything still on the board
    apiFetch<Record<string, number>>("/api/applications/summary")
      .then((summary) => {
        const active = ACTIVE_STATUSES.reduce((sum, status) => sum + (summary[status] ?? 0), 0);
        setCounts((prev) => ({ ...prev, applications: active }));
      })
      .catch((err) => console.warn("[badges] applications count failed:", err));
  }, []);

  return counts;
}
