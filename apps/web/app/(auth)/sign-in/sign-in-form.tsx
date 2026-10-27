"use client";

import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/shared/button";
import { authApi } from "@/features/auth/api";
import { ApiError } from "@/lib/api/client";

/** Only same-site paths are honoured as ?next= targets (no open redirect). */
function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/briefing";
}

const inputStyle = {
  background: "var(--surface)",
  borderColor: "var(--border)",
  color: "var(--text-primary)",
};

export function SignInForm() {
  const params = useSearchParams();
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
      window.location.assign(safeNext(params.get("next")));
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError("Too many attempts. Wait a few minutes and try again.");
      } else if (err instanceof ApiError && err.status === 401) {
        setError("Wrong email or password.");
      } else {
        console.error("[sign-in] failed:", err);
        setError("Couldn't reach the server. Try again.");
      }
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-xl border p-6 space-y-4"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <label className="block">
        <span className="block text-xs mb-1.5" style={{ color: "var(--text-muted)" }}>
          Email
        </span>
        <input
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full h-10 px-3 rounded-md border text-sm outline-none focus:border-[var(--accent)]"
          style={inputStyle}
        />
      </label>
      <label className="block">
        <span className="block text-xs mb-1.5" style={{ color: "var(--text-muted)" }}>
          Password
        </span>
        <input
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full h-10 px-3 rounded-md border text-sm outline-none focus:border-[var(--accent)]"
          style={inputStyle}
        />
      </label>

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
