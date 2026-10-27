"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";

/** Shown by a route's loading.tsx while its Server Component fetches data. */
export function RouteLoading({ label }: { label: string }) {
  return (
    <div className="wide-container px-6 lg:px-8 py-24 flex items-center justify-center gap-3">
      <Loader2 className="h-4 w-4 animate-spin" style={{ color: "var(--text-muted)" }} />
      <span className="text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </span>
    </div>
  );
}

/** Body of a route's error.tsx: the API failed — say so instead of showing an empty page. */
export function RouteError({
  error,
  retry,
  title,
}: {
  error: Error & { digest?: string };
  retry: () => void;
  title: string;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="max-w-[640px] mx-auto px-6 lg:px-8 py-24 text-center">
      <p className="font-editorial text-2xl" style={{ color: "var(--text-secondary)" }}>
        {title}
      </p>
      <p className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>
        {error.message || "An unexpected error occurred."}
      </p>
      <button onClick={() => retry()} className="mt-6 text-sm transition-colors" style={{ color: "var(--accent)" }}>
        Try again
      </button>
    </div>
  );
}
