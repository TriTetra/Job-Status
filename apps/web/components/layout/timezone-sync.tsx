"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export const TZ_COOKIE = "careeros_tz";

/**
 * Stores the browser's time zone in a cookie so server-rendered text ("Good morning",
 * "Wrapping up the week") follows the user's clock, not the server's. Refreshes once
 * when the zone is new or changed.
 */
export function TimezoneSync() {
  const router = useRouter();
  useEffect(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!tz) return;
    const current = document.cookie.split("; ").find((c) => c.startsWith(`${TZ_COOKIE}=`))?.split("=")[1];
    if (current && decodeURIComponent(current) === tz) return;
    document.cookie = `${TZ_COOKIE}=${encodeURIComponent(tz)}; path=/; max-age=31536000; samesite=lax`;
    router.refresh();
  }, [router]);
  return null;
}
