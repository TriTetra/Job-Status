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
      <div className="w-full max-w-xl">
        <StepWelcome />
      </div>
    );
  }

  // READY — shouldn't land here (middleware redirects to /briefing), but just in case
  if (step === "READY") {
    router.replace("/briefing");
    return null;
  }

  const goalsData = status?.goals;

  return (
    <WizardShell currentState={step as OnboardingState}>
      {step === "IDENTITY" && (
        <StepIdentity
          initialData={status?.profile_data}
          onComplete={() => router.push("/onboarding?step=GOALS")}
        />
      )}
      {step === "GOALS" && (
        <StepGoals
          initialData={status?.goals}
          onComplete={() => router.push("/onboarding?step=EVIDENCE")}
        />
      )}
      {step === "EVIDENCE" && (
        <StepEvidence
          onComplete={() => router.push("/onboarding?step=CONNECTIONS")}
        />
      )}
      {step === "BUILDING" && (
        <StepBuilding
          onComplete={() => router.push("/briefing")}
        />
      )}
      {step === "CONNECTIONS" && (
        <div className="text-center py-16 space-y-4">
          <p className="text-lg font-light" style={{ color: "var(--text-primary)" }}>
            Connections step
          </p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Coming soon — we&apos;re building this now.
          </p>
          <button
            onClick={async () => {
              const next = await onboardingApi.advance();
              if (next.state === "READY") {
                router.push("/briefing");
              } else {
                router.push(`/onboarding?step=${next.state}`);
              }
            }}
            className="mt-4 px-6 py-2.5 rounded-lg text-sm font-medium"
            style={{ background: "var(--accent)", color: "var(--accent-fg)" }}
          >
            Skip for now
          </button>
        </div>
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
