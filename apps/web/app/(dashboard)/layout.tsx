import { redirect, unstable_rethrow } from "next/navigation";
import { type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { getOnboardingState } from "@/features/onboarding/server";
import { stepUrl } from "@/features/onboarding/state-machine";
import type { OnboardingState } from "@/features/onboarding/types";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  // proxy.ts guarantees a signed-in user here
  let state: OnboardingState = "NOT_STARTED";
  try {
    state = await getOnboardingState();
  } catch (err) {
    unstable_rethrow(err); // let Next.js handle its own control-flow errors (dynamic rendering, redirects)
    // API unreachable — send to onboarding rather than render an empty dashboard
    console.error("[dashboard] onboarding state fetch failed:", err);
  }
  if (state !== "READY") redirect(stepUrl(state));

  return <AppShell>{children}</AppShell>;
}
