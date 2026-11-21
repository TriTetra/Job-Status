"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { authApi } from "@/features/auth/api";
import { AccountForm } from "@/features/auth/account-form";

type InviteState = { status: "checking" } | { status: "invalid" } | { status: "valid"; email: string | null };

/** Sign-up with a single-use invite link; signs the new user in and starts onboarding. */
export function InviteForm({ token }: { token: string }) {
  const [state, setState] = useState<InviteState>({ status: "checking" });

  useEffect(() => {
    authApi
      .checkInvite(token)
      .then((r) => setState(r.valid ? { status: "valid", email: r.email } : { status: "invalid" }))
      .catch(() => setState({ status: "invalid" }));
  }, [token]);

  if (state.status === "checking") return <div className="h-64" aria-busy="true" />;

  if (state.status === "invalid") {
    return (
      <div className="text-center space-y-3">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          This invite link is invalid, already used or expired. Ask for a new one.
        </p>
        <Link href="/sign-in" className="text-sm underline underline-offset-4" style={{ color: "var(--accent)" }}>
          Already have an account? Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-center" style={{ color: "var(--text-secondary)" }}>
        You&apos;re invited. Create your account to get started.
      </p>
      <AccountForm
        submitLabel="Create account"
        lockedEmail={state.email}
        onSubmit={async (account) => {
          await authApi.acceptInvite(token, account);
          window.location.assign("/onboarding");
        }}
      />
    </div>
  );
}
