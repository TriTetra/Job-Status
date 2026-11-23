"use client";

import { useCallback, useEffect, useState } from "react";
import { Mail } from "lucide-react";
import { ApiError } from "@/lib/api/client";
import { MailSignals } from "@/components/applications/mail-signals";
import { mailApi, PROBLEM_LABEL, type MailStatus } from "@/features/settings/mail";
import { Row, Section, UnderlineInput } from "./kit";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-40";
const KNOWN = /@(gmail|googlemail|yahoo|ymail|icloud|me|mac|outlook|hotmail|live|msn|yandex|mail|gmx|web|zoho|fastmail|aol)\./i;

function detail(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null;
  try {
    const d = JSON.parse(err.body)?.detail;
    return typeof d === "string" ? d : null;
  } catch {
    return null;
  }
}

function ago(iso: string | null): string {
  if (!iso) return "not checked yet";
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60_000);
  if (mins < 60) return `checked ${Math.max(1, mins)} min ago`;
  const h = Math.round(mins / 60);
  return h < 48 ? `checked ${h} h ago` : `checked ${Math.round(h / 24)} days ago`;
}

/** Mailbox: employers' answers to your applications, found and filed for you. */
export function MailSection() {
  const [st, setSt] = useState<MailStatus | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [host, setHost] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const needsHost = email.includes("@") && email.split("@")[1]?.includes(".") && !KNOWN.test(email);

  const load = useCallback(async () => {
    try {
      setSt(await mailApi.status());
    } catch {
      setSt(null);
    }
  }, []);
  useEffect(() => {
    mailApi.status().then(setSt).catch(() => setSt(null));
  }, []);

  const connect = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setNote(null);
    try {
      setSt(await mailApi.connect(email.trim(), password, needsHost ? host : undefined));
      setPassword("");
      setNote({ ok: true, text: "Connected. Aplio checks it at every refresh (about every 6 hours)." });
    } catch (err) {
      setNote({ ok: false, text: detail(err) ?? "Couldn't connect. Try again." });
    } finally {
      setBusy(false);
    }
  };

  const check = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await mailApi.check();
      setSt(r);
      const found = Number(r.result?.about_applications ?? 0);
      setNote({ ok: !r.result?.problem, text: r.result?.problem ? String(r.result.problem)
        : found ? `Found ${found} answer${found > 1 ? "s" : ""} about your applications.` : "Nothing new about your applications." });
    } catch {
      setNote({ ok: false, text: "The check didn't finish. Try again in a moment." });
    } finally {
      setBusy(false);
    }
  };

  const forget = async () => {
    setBusy(true);
    try {
      await mailApi.disconnect();
      setNote({ ok: true, text: "Disconnected. Everything found in your mail is forgotten." });
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section title="Mailbox">
      <Row label="Answers from employers"
           hint="Rejections, interview invites and offers move your applications by themselves; anything unsure waits for you">
        {st === null ? (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Loading…</span>
        ) : st.connected ? (
          <span className="flex flex-wrap items-center gap-x-4 gap-y-2 min-w-0">
            <span className="inline-flex items-center gap-1.5 text-sm" style={{ color: "var(--success)" }}>
              <Mail className="h-3.5 w-3.5" /> {st.email}
            </span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>{ago(st.last_checked)}</span>
            <button className={textBtn} style={{ color: "var(--accent)" }} disabled={busy} onClick={check}>
              {busy ? "Checking…" : "Check now"}
            </button>
            <button className={textBtn} style={{ color: "var(--danger)" }} disabled={busy} onClick={forget}>
              Disconnect and forget
            </button>
          </span>
        ) : (
          <form onSubmit={connect} className="space-y-3">
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Aplio reads only mail about companies you applied to, never marks anything read, and keeps just the
              subject, the kind of answer and one quoted sentence. Use an <b>app password</b>, not your real one:
              in Gmail, turn on 2-Step Verification, then create one at{" "}
              <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer"
                 className="underline underline-offset-2" style={{ color: "var(--accent)" }}>Google Account → App passwords</a>.
              You can revoke it there any time.
            </p>
            <UnderlineInput className="block" type="email" placeholder="you@gmail.com" value={email} autoComplete="email"
                            onChange={(e) => setEmail(e.target.value)} aria-label="E-mail address" />
            <UnderlineInput className="block" type="password" placeholder="App password" value={password} autoComplete="off"
                            onChange={(e) => setPassword(e.target.value)} aria-label="App password" />
            {needsHost && (
              <UnderlineInput className="block" placeholder="IMAP server, e.g. imap.example.com" value={host}
                              onChange={(e) => setHost(e.target.value)} aria-label="IMAP server" />
            )}
            <button type="submit" disabled={busy || !email.trim() || !password}
                    className="inline-flex items-center gap-2 h-8 px-3 rounded-lg text-sm font-semibold disabled:opacity-50"
                    style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              <Mail className="h-3.5 w-3.5" /> {busy ? "Testing the sign-in…" : "Connect mailbox"}
            </button>
          </form>
        )}
        {st?.problem && PROBLEM_LABEL[st.problem] && (
          <p className="text-xs mt-1.5" role="alert" style={{ color: "var(--danger)" }}>{PROBLEM_LABEL[st.problem]}</p>
        )}
        {note && (
          <p className="text-xs mt-1.5" role={note.ok ? "status" : "alert"} style={{ color: note.ok ? "var(--success)" : "var(--danger)" }}>
            {note.text}
          </p>
        )}
      </Row>
      {st?.connected && st.signals.length > 0 && (
        <Row label="Found in your mail" hint={st.pending ? `${st.pending} waiting for you` : "Most recent first"}>
          <MailSignals signals={st.signals} onChange={load} />
        </Row>
      )}
    </Section>
  );
}
