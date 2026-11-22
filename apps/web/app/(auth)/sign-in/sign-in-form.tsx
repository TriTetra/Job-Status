"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/shared/button";
import { authApi } from "@/features/auth/api";
import { AccountForm, AuthField, authErrorMessage } from "@/features/auth/account-form";
import { ApiError } from "@/lib/api/client";

/** Only same-site paths are honoured as ?next= targets (no open redirect). */
function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/briefing";
}

/**
 * Sign in — or, while the site has no account yet, create the first one
 * (it becomes the admin who invites everyone else).
 */
export function SignInForm() {
  const params = useSearchParams();
  const [setupNeeded, setSetupNeeded] = useState<boolean | null>(null);

  useEffect(() => {
    authApi
      .setupStatus()
      .then((s) => setSetupNeeded(s.needed))
      .catch(() => setSetupNeeded(false));
  }, []);

  if (setupNeeded === null) return <div className="h-64" aria-busy="true" />;

  if (setupNeeded) {
    return (
      <div className="space-y-4">
        <div className="text-center space-y-1.5">
          <h1 className="text-base font-medium" style={{ color: "var(--text-primary)" }}>
            Create the admin account
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            This workspace has no accounts yet, so this screen appears once. After this, everyone signs in
            with email and password, and new people join through invite links you create in Settings.
          </p>
        </div>
        <AccountForm
          submitLabel="Create admin account"
          onSubmit={async (account) => {
            await authApi.setup(account);
            window.location.assign("/onboarding");
          }}
        />
      </div>
    );
  }

  return <PasswordSignIn next={safeNext(params.get("next"))} />;
}

function PasswordSignIn({ next }: { next: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await authApi.login(email, password);
      // Full navigation so server components re-render with the new session cookie
      window.location.assign(next);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? "Wrong email or password." : authErrorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-xl border p-6 space-y-4"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <AuthField
        label="Email"
        type="email"
        autoComplete="username"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <AuthField
        label="Password"
        type="password"
        autoComplete="current-password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      {error && (
        <p className="text-sm" role="alert" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      <Button type="submit" loading={busy} disabled={busy} className="w-full">
        Sign in
      </Button>
    </form>
  );
}
