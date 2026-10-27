"use client";

import { RouteError } from "@/components/shared/route-states";

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  return <RouteError error={error} retry={unstable_retry} title="Companies couldn't be loaded." />;
}
