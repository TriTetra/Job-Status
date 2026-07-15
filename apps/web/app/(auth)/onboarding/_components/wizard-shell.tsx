"use client";

import { type ReactNode } from "react";
import { AplioLogo } from "@/components/shared/aplio-logo";
import { STEP_ORDER, STEP_META, type OnboardingState } from "@/features/onboarding";
import { cn } from "@/lib/utils";

interface WizardShellProps {
  currentState: OnboardingState;
  children: ReactNode;
}

export function WizardShell({ currentState, children }: WizardShellProps) {
  const currentIdx = STEP_ORDER.indexOf(currentState as typeof STEP_ORDER[number]);

  return (
    <div className="w-full max-w-xl">
      {/* Wordmark + step counter in one compact row */}
      <div className="flex items-center justify-between mb-4">
        <AplioLogo variant="wordmark" size="md" />
        {currentIdx >= 0 && (
          <p className="text-[11px] font-medium tracking-widest uppercase" style={{ color: "var(--text-muted)" }}>
            Step {currentIdx + 1} / {STEP_ORDER.length}
          </p>
        )}
      </div>

      {/* Step progress */}
      <div className="flex items-center gap-1 mb-5">
        {STEP_ORDER.map((step, i) => {
          const done = i < currentIdx;
          const active = i === currentIdx;
          return (
            <div
              key={step}
              className={cn(
                "h-0.5 flex-1 rounded-full transition-all duration-300",
                done ? "opacity-100" : active ? "opacity-60" : "opacity-15"
              )}
              style={{ background: "var(--accent)" }}
            />
          );
        })}
      </div>

      {/* Content */}
      {children}
    </div>
  );
}
