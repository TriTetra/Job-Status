"use client";

import { useState } from "react";
import { KIND_LABEL, mailApi, type MailSignal } from "@/features/settings/mail";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-40";
const STATUS_WORD: Record<string, string> = {
  applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected",
};

function when(iso: string | null): string {
  if (!iso) return "";
  const days = Math.round((Date.now() - Date.parse(iso)) / 86_400_000);
  return days <= 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`;
}

/** What Aplio found in the mailbox: unsure answers to confirm, and the moves it made. */
export function MailSignals({ signals, onChange, limit = 8 }: {
  signals: MailSignal[];
  onChange: () => void;
  limit?: number;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  const [failed, setFailed] = useState<number | null>(null);
  const shown = signals.filter((s) => s.state === "pending" || s.state === "applied").slice(0, limit);
  if (shown.length === 0) return null;

  const act = async (s: MailSignal, action: "confirm" | "dismiss") => {
    setBusy(s.id);
    setFailed(null);
    try {
      await mailApi.resolve(s.id, action);
      onChange();
    } catch {
      setFailed(s.id);
    } finally {
      setBusy(null);
    }
  };

  return (
    <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
      {shown.map((s) => (
        <li key={s.id} className="py-3 text-sm" style={{ borderColor: "var(--border)" }}>
          <p style={{ color: "var(--text-primary)" }}>
            <span className="font-medium">{s.company ?? s.from_domain}</span>
            {s.title ? <span style={{ color: "var(--text-secondary)" }}> · {s.title}</span> : null}
            <span style={{ color: "var(--text-muted)" }}> · {when(s.received_at)}</span>
          </p>
          <p className="mt-0.5" style={{ color: "var(--text-secondary)" }}>
            {s.state === "applied" ? (
              <>Moved to <b>{STATUS_WORD[s.status_after ?? ""] ?? s.status_after}</b>: {KIND_LABEL[s.kind].toLowerCase()} in your mail</>
            ) : s.status_after ? (
              <>Looks like {KIND_LABEL[s.kind].toLowerCase()}. Move it to <b>{STATUS_WORD[s.status_after] ?? s.status_after}</b>?</>
            ) : (
              <>{KIND_LABEL[s.kind]}: check the e-mail and answer them.</>
            )}
          </p>
          {s.evidence && (
            <p className="mt-1 text-xs italic line-clamp-2" style={{ color: "var(--text-muted)" }}>“{s.evidence}”</p>
          )}
          <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>Subject: {s.subject}</p>
          {s.state === "pending" && (
            <span className="mt-1.5 flex gap-4">
              {s.status_after && (
                <button className={textBtn} style={{ color: "var(--accent)" }} disabled={busy === s.id} onClick={() => act(s, "confirm")}>
                  Yes, move it
                </button>
              )}
              <button className={textBtn} style={{ color: "var(--text-muted)" }} disabled={busy === s.id} onClick={() => act(s, "dismiss")}>
                {s.status_after ? "No, leave it" : "Done"}
              </button>
            </span>
          )}
          {failed === s.id && <p className="mt-1 text-xs" role="alert" style={{ color: "var(--danger)" }}>That didn&apos;t save. Try again.</p>}
        </li>
      ))}
    </ul>
  );
}
