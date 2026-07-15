import { type ReactNode } from "react";

export const metadata = {
  title: "Aplio — Getting started",
};

export default function OnboardingLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="h-screen w-screen flex flex-col overflow-hidden"
      style={{ background: "var(--background)" }}
    >
      {/* Scrollable content area — edge case'ler için */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="min-h-full flex items-center justify-center px-4 py-3">
          <div className="w-full max-w-xl">{children}</div>
        </div>
      </div>
    </div>
  );
}
