"use client";

import { useCallback, useEffect, useState } from "react";
import { authApi } from "@/features/auth/api";
import { authErrorMessage, MIN_PASSWORD } from "@/features/auth/account-form";
import type { CreatedInvite, Invite } from "@/features/auth/types";
import { Row, Section, UnderlineInput } from "./kit";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-50";

/** Change your own password; other browsers are signed out. */
export function PasswordRow() {
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const save = async () => {
    if (next.length < MIN_PASSWORD) return setMessage({ ok: false, text: `At least ${MIN_PASSWORD} characters.` });
    setBusy(true);
    setMessage(null);
    try {
      await authApi.changePassword(current, next);
      setOpen(false);
      setCurrent("");
      setNext("");
      setMessage({ ok: true, text: "Password changed. Other devices were signed out." });
    } catch (err) {
      setMessage({ ok: false, text: authErrorMessage(err) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Row label="Password" hint="Changing it signs out your other devices">
      {open ? (
        <span className="flex flex-wrap items-center gap-3">
          <UnderlineInput
            type="password"
            autoComplete="current-password"
            placeholder="Current password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
          <UnderlineInput
            type="password"
            autoComplete="new-password"
            placeholder={`New password (${MIN_PASSWORD}+)`}
            value={next}
            onChange={(e) => setNext(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
          />
          <button className={textBtn} style={{ color: "var(--accent)" }} onClick={save} disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
          <button className={textBtn} style={{ color: "var(--text-muted)" }} onClick={() => setOpen(false)}>
            Cancel
          </button>
        </span>
      ) : (
        <button className={textBtn} style={{ color: "var(--accent)" }} onClick={() => setOpen(true)}>
          Change password
        </button>
      )}
      {message && (
        <div className="text-xs mt-2" style={{ color: message.ok ? "var(--success)" : "var(--danger)" }}>
          {message.text}
        </div>
      )}
    </Row>
  );
}

const day = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });

/** Admins: single-use sign-up links for friends. */
export function InvitesSection() {
  const [invites, setInvites] = useState<Invite[]>([]);
  const [email, setEmail] = useState("");
  const [created, setCreated] = useState<CreatedInvite | null>(null);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    authApi.listInvites().then(setInvites).catch(() => setInvites([]));
  }, []);
  useEffect(refresh, [refresh]);

  const create = async () => {
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      setCreated(await authApi.createInvite(email.trim() || undefined));
      setEmail("");
      refresh();
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const copy = async () => {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const pending = invites.filter((i) => !i.used_at);
  const used = invites.filter((i) => i.used_at);

  return (
    <Section title="Invites">
      <Row label="New invite" hint="Single use, valid 7 days. Leave email empty for anyone with the link">
        <span className="flex flex-wrap items-center gap-3">
          <UnderlineInput
            type="email"
            placeholder="friend@example.com (optional)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
          />
          <button className={textBtn} style={{ color: "var(--accent)" }} onClick={create} disabled={busy}>
            {busy ? "Creating…" : "Create link"}
          </button>
        </span>
        {error && (
          <div className="text-xs mt-2" style={{ color: "var(--danger)" }}>
            {error}
          </div>
        )}
        {created && (
          <div className="mt-3 text-xs space-y-1.5">
            <div style={{ color: "var(--text-muted)" }}>
              Send this link{created.email ? ` to ${created.email}` : ""}. It is shown only once.
            </div>
            <div className="flex items-center gap-3 min-w-0">
              <code className="truncate min-w-0 flex-1" style={{ color: "var(--text-primary)" }}>
                {created.url}
              </code>
              <button className={`${textBtn} shrink-0`} style={{ color: "var(--accent)" }} onClick={copy}>
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
        )}
      </Row>

      {pending.length > 0 && (
        <Row label="Pending" hint="Not used yet">
          <ul className="space-y-2">
            {pending.map((i) => (
              <li key={i.id} className="flex items-center gap-4 text-sm">
                <span style={{ color: "var(--text-primary)" }}>{i.email ?? "Anyone with the link"}</span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  expires {day(i.expires_at)}
                </span>
                <button
                  className={textBtn}
                  style={{ color: "var(--danger)" }}
                  onClick={async () => {
                    await authApi.revokeInvite(i.id).catch(() => undefined);
                    refresh();
                  }}
                >
                  Revoke
                </button>
              </li>
            ))}
          </ul>
        </Row>
      )}

      {used.length > 0 && (
        <Row label="Joined">
          <ul className="space-y-1.5">
            {used.map((i) => (
              <li key={i.id} className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {i.used_by_email ?? i.email ?? "—"}
                <span className="text-xs ml-3" style={{ color: "var(--text-muted)" }}>
                  {i.used_at ? day(i.used_at) : ""}
                </span>
              </li>
            ))}
          </ul>
        </Row>
      )}
    </Section>
  );
}
