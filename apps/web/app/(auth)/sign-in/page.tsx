import { Suspense } from "react";
import { Brand } from "../_components/brand";
import { SignInForm } from "./sign-in-form";

export default function SignInPage() {
  return (
    <div className="w-full max-w-md">
      <Brand />

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
