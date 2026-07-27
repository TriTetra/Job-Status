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
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {/* flex-col + child my-auto = safe vertical centering (taşarsa üstten başlar, logo kesilmez) */}
        <div className="min-h-full flex flex-col items-center px-4 py-6">
          <div className="w-full max-w-5xl my-auto">{children}</div>
        </div>
      </div>
    </div>
  );
}
