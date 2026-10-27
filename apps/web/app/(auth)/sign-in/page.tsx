import { Suspense } from "react";
import { SignInForm } from "./sign-in-form";

export default function SignInPage() {
  return (
    <div className="w-full max-w-md">
      <div className="flex flex-col items-center mb-10">
        <div
          className="text-[42px] tracking-[0.14em] font-extralight leading-none mb-3"
          style={{
            fontFamily: "'Outfit', 'Inter Variable', Inter, system-ui, sans-serif",
            color: "var(--text-primary)",
            textIndent: "0.14em",
          }}
        >
          Aplio
        </div>
        <div className="w-8 mb-3" style={{ height: 1.5, background: "var(--accent)" }} />
        <p className="text-sm font-editorial italic" style={{ color: "var(--text-muted)" }}>
          Your career, understood.
        </p>
      </div>

      {/* useSearchParams (the ?next= target) needs a Suspense boundary */}
      <Suspense>
        <SignInForm />
      </Suspense>

      <p className="text-center text-xs mt-6" style={{ color: "var(--text-muted)" }}>
        Private workspace — accounts are created by invitation.
      </p>
    </div>
  );
}
