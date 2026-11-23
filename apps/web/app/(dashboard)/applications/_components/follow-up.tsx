"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { applicationsApi, type Application, type FollowUpDraft } from "@/features/applications/api";
import { shortDate } from "@/features/applications/format";

const textBtn = "text-xs underline underline-offset-4 transition-colors cursor-pointer disabled:opacity-40";

/** The follow-up that is due: a draft from your evidence that you send yourself, then mark sent. */
export function FollowUp({ app, onChanged }: { app: Application; onChanged: () => void }) {
  const fu = app.follow_up;
  const [draft, setDraft] = useState<FollowUpDraft | null>(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  if (!fu || (!fu.due && !fu.sent)) return null;

  if (!fu.due) {
    return (
      <p className="mt-4 text-sm" style={{ color: "var(--text-muted)" }}>
        You followed up {fu.last_sent_at ? shortDate(fu.last_sent_at) : ""}
        {fu.sent > 1 ? " twice. Aplio won't suggest another one." : ". Aplio suggests one last check-in a week later if there's still no answer."}
      </p>
    );
  }

  const run = async (what: string, fn: () => Promise<void>) => {
    setBusy(what);
    setNote(null);
    try {
      await fn();
    } catch {
      setNote({ ok: false, text: "That didn't work. Try again." });
    } finally {
      setBusy(null);
    }
  };

  const write = (refresh = false) => run(refresh ? "rewrite" : "write", async () => {
    const d = await applicationsApi.followUpDraft(app.url, refresh);
    setDraft(d);
    setBody(d.body);
  });

  const copy = () => run("copy", async () => {
    await navigator.clipboard.writeText(`Subject: ${draft?.subject}\n\n${body}`);
    setNote({ ok: true, text: "Copied. Paste it into your e-mail or a LinkedIn message to the recruiter." });
  });

  const sent = () => run("sent", async () => {
    if (!draft) return;
    await applicationsApi.followUpSent(draft.id);
    setDraft(null);
    onChanged();
  });

  const skip = () => run("skip", async () => {
    await applicationsApi.followUpSkip(app.url);
    onChanged();
  });

  const mailto = draft ? `mailto:?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(body)}` : "";
  const last = fu.due === 2;

  return (
    <div className="mt-5">
      <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
        No answer for {fu.days_waiting} days.{" "}
        {last ? "One last, short check-in is worth it; after that, let it go." : "A short, specific follow-up to the recruiter often gets one."}
      </p>
      {!draft ? (
        <span className="mt-2 flex flex-wrap items-center gap-4">
          <button onClick={() => write()} disabled={busy !== null}
                  className="inline-flex items-center gap-2 h-8 px-3 rounded-lg text-sm font-semibold disabled:opacity-50"
                  style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
            {busy === "write" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            {busy === "write" ? "Writing from your evidence…" : last ? "Draft the check-in" : "Draft a follow-up"}
          </button>
          <button className={textBtn} style={{ color: "var(--text-muted)" }} disabled={busy !== null} onClick={skip}>
            Don&apos;t follow up
          </button>
        </span>
      ) : (
        <div className="mt-3">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Subject</p>
          <p className="text-sm" style={{ color: "var(--text-primary)" }}>{draft.subject}</p>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={9} aria-label="Follow-up text"
                    className="mt-2 w-full rounded-lg border bg-transparent p-3 text-sm leading-relaxed outline-none focus:border-[var(--accent)] resize-y"
                    style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
          {draft.check.length > 0 && (
            <p className="mt-1 text-xs" style={{ color: "var(--warning, var(--danger))" }}>
              Check before sending: {draft.check.join("; ")}.
            </p>
          )}
          <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
            {draft.drafted_by === "template" ? "A plain template (the AI writer is off)." : "Written only from your evidence."} Add the recruiter&apos;s name if you know it. Aplio never sends it for you.
          </p>
          <span className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
            <button onClick={copy} disabled={busy !== null}
                    className="h-8 px-3 rounded-lg border text-sm hover:bg-[var(--surface)] disabled:opacity-50"
                    style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}>Copy</button>
            <a href={mailto} className="h-8 px-3 rounded-lg border text-sm inline-flex items-center hover:bg-[var(--surface)]"
               style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}>Open in mail</a>
            <button onClick={sent} disabled={busy !== null}
                    className="inline-flex items-center gap-2 h-8 px-3 rounded-lg text-sm font-semibold disabled:opacity-50"
                    style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>I sent it</button>
            <button className={textBtn} style={{ color: "var(--text-muted)" }} disabled={busy !== null} onClick={() => write(true)}>
              {busy === "rewrite" ? "Rewriting…" : "Rewrite"}
            </button>
          </span>
        </div>
      )}
      {note && (
        <p className="mt-2 text-xs" role={note.ok ? "status" : "alert"} style={{ color: note.ok ? "var(--success)" : "var(--danger)" }}>{note.text}</p>
      )}
    </div>
  );
}
