"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { onboardingApi } from "@/features/onboarding";
import type { OnboardingStatus } from "@/features/onboarding";
import { WizardShell } from "./_components/wizard-shell";
import { StepWelcome } from "./_components/step-welcome";
import { StepIdentity } from "./_components/step-identity";
import { StepGoals } from "./_components/step-goals";
import { StepEvidence } from "./_components/step-evidence";
import { StepBuilding } from "./_components/step-building";
import { StepConnections } from "./_components/step-connections";
import type { OnboardingState } from "@/features/onboarding";

function OnboardingContent() {
  const router = useRouter();
  const params = useSearchParams();
  const step = (params.get("step") ?? "WELCOME") as OnboardingState | "WELCOME";

  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    onboardingApi
      .getState()
      .then(setStatus)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        className="w-full max-w-xl flex items-center justify-center py-24 text-sm"
        style={{ color: "var(--text-muted)" }}
      >
        Loading…
      </div>
    );
  }

  // Welcome screen (no step param)
  if (step === "WELCOME" || step === "NOT_STARTED") {
    return (
      <div className="w-full max-w-xl mx-auto">
        <StepWelcome />
      </div>
    );
  }

  // READY — shouldn't land here (middleware redirects to /briefing), but just in case
  if (step === "READY") {
    router.replace("/briefing");
    return null;
  }

  // BUILDING — full-screen split layout
  if (step === "BUILDING") {
    return <StepBuilding onComplete={() => router.push("/briefing")} />;
  }

  // GOALS — editorial two-column (wide layout, like BUILDING)
  if (step === "GOALS") {
    return (
      <StepGoals
        initialData={status?.preferences ?? undefined}
        onComplete={() => router.push("/onboarding?step=EVIDENCE")}
      />
    );
  }

  return (
    <WizardShell currentState={step as OnboardingState}>
      {step === "IDENTITY" && (
        <StepIdentity
          initialData={status?.profile_data}
          onComplete={() => router.push("/onboarding?step=GOALS")}
        />
      )}
      {step === "EVIDENCE" && (
        <StepEvidence
          onComplete={() => router.push("/onboarding?step=CONNECTIONS")}
        />
      )}
      {step === "CONNECTIONS" && (
        <StepConnections
          onComplete={async () => {
            await onboardingApi.advance();   // CONNECTIONS → BUILDING (state machine tutarlılığı)
            router.push("/onboarding?step=BUILDING");
          }}
        />
      )}
    </WizardShell>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense>
      <OnboardingContent />
    </Suspense>
  );
}
