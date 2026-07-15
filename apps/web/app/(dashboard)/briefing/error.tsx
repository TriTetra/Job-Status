"use client";

import { useEffect } from "react";

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="max-w-[640px] mx-auto px-6 lg:px-8 py-24 text-center">
      <p className="font-editorial text-2xl" style={{ color: "var(--text-secondary)" }}>
        Something interrupted today&apos;s briefing.
      </p>
      <p className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={() => unstable_retry()}
        className="mt-6 text-sm transition-colors"
        style={{ color: "var(--accent)" }}
      >
        Try again
      </button>
    </div>
  );
}
