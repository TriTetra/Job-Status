"use client";

import { useState, type FormEvent, type InputHTMLAttributes } from "react";
import { Button } from "@/components/shared/button";
import { ApiError } from "@/lib/api/client";

import { apiDetail } from "./api";
import type { NewAccount } from "./types";

// Must match careeros/identity/auth/passwords.py MIN_LENGTH
export const MIN_PASSWORD = 12;

const inputStyle = {
  background: "var(--surface)",
  borderColor: "var(--border)",
  color: "var(--text-primary)",
};

export function AuthField({ label, ...props }: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-xs mb-1.5" style={{ color: "var(--text-muted)" }}>
        {label}
      </span>
      <input
        {...props}
        className="w-full h-10 px-3 rounded-md border text-sm outline-none focus:border-[var(--accent)] disabled:opacity-60"
        style={inputStyle}
      />
    </label>
  );
}

/** The user-facing message for a failed auth request. */
export function authErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 429) return "Too many attempts. Wait a few minutes and try again.";
    return apiDetail(err.body) ?? "Something went wrong. Try again.";
  }
  console.error("[auth] request failed:", err);
  return "Couldn't reach the server. Try again.";
}

/** Name, email, password twice — used by first-account setup and invite sign-up. */
export function AccountForm({
  submitLabel,
  lockedEmail,
  onSubmit,
}: {
  submitLabel: string;
  lockedEmail?: string | null;
  onSubmit: (account: NewAccount) => Promise<void>;
}) {
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [email, setEmail] = useState(lockedEmail ?? "");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (password.length < MIN_PASSWORD) return setError(`Use at least ${MIN_PASSWORD} characters.`);
    if (password !== confirm) return setError("The passwords don't match.");
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        email: lockedEmail ?? email,
        password,
        first_name: first.trim() || undefined,
        last_name: last.trim() || undefined,
      });
    } catch (err) {
      setError(authErrorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="rounded-xl border p-6 space-y-4"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <div className="grid grid-cols-2 gap-3">
        <AuthField label="First name" autoComplete="given-name" value={first} onChange={(e) => setFirst(e.target.value)} />
        <AuthField label="Last name" autoComplete="family-name" value={last} onChange={(e) => setLast(e.target.value)} />
      </div>
      <AuthField
        label="Email"
        type="email"
        autoComplete="username"
        required
        value={lockedEmail ?? email}
        disabled={!!lockedEmail}
        onChange={(e) => setEmail(e.target.value)}
      />
      <AuthField
        label={`Password (min ${MIN_PASSWORD} characters)`}
        type="password"
        autoComplete="new-password"
        required
        minLength={MIN_PASSWORD}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <AuthField
        label="Repeat password"
        type="password"
        autoComplete="new-password"
        required
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
      />

      {error && (
        <p className="text-sm" role="alert" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      <Button type="submit" loading={busy} disabled={busy} className="w-full">
        {submitLabel}
      </Button>
    </form>
  );
}
