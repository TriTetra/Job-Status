"use client";

import { useRouter } from "next/navigation";
import { useMe } from "@/features/auth/use-me";

export function StepWelcome() {
  const router = useRouter();
  const me = useMe();
  const name = me?.first_name ?? "there";

  return (
    <div className="text-center">
      <h1
        className="text-4xl font-light tracking-tight mb-4"
        style={{ color: "var(--text-primary)" }}
      >
        Welcome, {name}.
      </h1>
      <p
        className="text-base mb-10 leading-relaxed max-w-sm mx-auto"
        style={{ color: "var(--text-muted)" }}
      >
        Let&apos;s build your career narrative. It takes about{" "}
        <span style={{ color: "var(--text-primary)" }}>3 minutes</span>.
      </p>

      <div
        className="w-8 mx-auto mb-10"
        style={{ height: 1.5, background: "var(--accent)" }}
      />

      <p
        className="text-sm italic mb-10"
        style={{ color: "var(--text-muted)", fontFamily: "var(--font-editorial, serif)" }}
      >
        Your career, understood.
      </p>

      <button
        onClick={() => router.push("/onboarding?step=IDENTITY")}
        className="w-full py-3 px-6 rounded-lg text-sm font-medium tracking-wide transition-all"
        style={{
          background: "var(--accent)",
          color: "var(--accent-fg)",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.9")}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
      >
        Get started
      </button>
    </div>
  );
}
