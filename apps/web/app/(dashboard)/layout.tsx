import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { AppShell } from "@/components/layout/app-shell";
import { type ReactNode } from "react";
import { getOnboardingState, STATE_TO_URL } from "@/lib/db/onboarding";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const { userId } = await auth();

  if (userId) {
    let state = "NOT_STARTED";
    try {
      state = await getOnboardingState(userId);
    } catch (err) {
      console.error("[dashboard] onboarding state fetch failed:", err);
      // DB unreachable — assume not onboarded, send to onboarding
    }
    if (state !== "READY") {
      redirect(STATE_TO_URL[state] ?? "/onboarding?step=IDENTITY");
    }
  }

  return <AppShell>{children}</AppShell>;
}
