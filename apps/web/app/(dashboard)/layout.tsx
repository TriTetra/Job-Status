import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { AppShell } from "@/components/layout/app-shell";
import { type ReactNode } from "react";

const STATE_TO_URL: Record<string, string> = {
  NOT_STARTED: "/onboarding?step=IDENTITY",
  IDENTITY:    "/onboarding?step=IDENTITY",
  GOALS:       "/onboarding?step=GOALS",
  EVIDENCE:    "/onboarding?step=EVIDENCE",
  CONNECTIONS: "/onboarding?step=CONNECTIONS",
  BUILDING:    "/onboarding?step=BUILDING",
};

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const { userId } = await auth();

  if (userId) {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/onboarding/state`, {
        headers: { "x-user-id": userId },
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      });

      if (res.ok) {
        const { state } = (await res.json()) as { state: string };
        if (state !== "READY") {
          redirect(STATE_TO_URL[state] ?? "/onboarding?step=IDENTITY");
        }
      }
    } catch {
      // Backend unreachable — fail open, don't block the dashboard
    }
  }

  return <AppShell>{children}</AppShell>;
}
