import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { AppShell } from "@/components/layout/app-shell";
import { type ReactNode } from "react";
import { getOnboardingState, STATE_TO_URL } from "@/lib/db/onboarding";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const { userId } = await auth();

  if (userId) {
    try {
      const state = await getOnboardingState(userId);
      if (state !== "READY") {
        redirect(STATE_TO_URL[state] ?? "/onboarding?step=IDENTITY");
      }
    } catch {
      // DB unreachable — fail open, don't block the dashboard
    }
  }

  return <AppShell>{children}</AppShell>;
}
