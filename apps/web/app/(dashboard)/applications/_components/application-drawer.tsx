"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, X } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { safeHttpUrl } from "@/lib/utils";
import { applicationsApi, type Application, type ApplicationStatus } from "@/features/applications/api";
import { companyOf, REC_COLOR, STAGES, STATUS_LABEL, shortDate } from "@/features/applications/format";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

/** One application: where it stands, what to do next, your notes, and everything that happened. */
export function ApplicationDrawer({ app, onClose, onMove, onChanged, onRemoved }: {
  app: Application;
  onClose: () => void;
  onMove: (url: string, status: ApplicationStatus) => Promise<void>;
  onChanged: () => void;
  onRemoved: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  const [notes, setNotes] = useState(app.notes ?? "");
  const [noteState, setNoteState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [confirmRemove, setConfirmRemove] = useState(false);

  useEffect(() => {
    closeRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeRef.current();
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      opener?.focus?.();
    };
  }, []);

  const saveNotes = async () => {
    if ((app.notes ?? "") === notes.trim()) return;
    setNoteState("saving");
    try {
      await applicationsApi.setNotes(app.url, notes);
      setNoteState("saved");
      onChanged();
    } catch {
      setNoteState("error");
    }
  };

  const remove = async () => {
    await applicationsApi.remove(app.url);
    onRemoved();
  };

  const closed = app.status === "rejected" || app.status === "withdrawn";
  const stageIndex = STAGES.findIndex((s) => s.id === app.status);
  const next = STAGES[stageIndex]?.next;
  const posting = safeHttpUrl(app.application_url);
  const events = [...app.history].reverse();

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 settings-scrim" onClick={onClose} aria-hidden="true" />
      <div ref={panelRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="app-title"
           className="drawer-panel absolute right-0 top-0 h-full w-full sm:w-[480px] flex flex-col border-l outline-none"
           style={{ background: "var(--background)", borderColor: "var(--border-strong)", boxShadow: "-30px 0 80px rgba(0,0,0,0.45)" }}>
        <header className="shrink-0 px-6 pt-6 pb-5 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-start gap-4">
            <CompanyLogo name={companyOf(app)} companyKey={app.company_key} jobUrl={app.url} size={52} />
            <div className="min-w-0 flex-1">
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{companyOf(app)}</p>
              <h2 id="app-title" className="font-serif-display text-[24px] leading-tight" style={{ color: "var(--text-primary)" }}>{app.title}</h2>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                {[app.remote ? "Remote" : app.location, app.applied_at ? `applied ${shortDate(app.applied_at)}` : null, app.posting_closed ? "posting closed" : null].filter(Boolean).join(" · ")}
              </p>
            </div>
            <button onClick={onClose} aria-label="Close" className="h-8 w-8 -mr-2 rounded-md flex items-center justify-center hover:bg-[var(--surface)]" style={{ color: "var(--text-muted)" }}>
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-6 py-6 space-y-8">
          {/* Where it stands */}
          <section>
            <p className={LABEL} style={LABEL_STYLE}>Stage</p>
            <ol className="mt-3 grid grid-cols-4 gap-1.5" aria-label="Pipeline stages">
              {STAGES.map((s, i) => {
                const done = !closed && i <= stageIndex;
                const current = s.id === app.status;
                return (
                  <li key={s.id}>
                    <button onClick={() => !current && onMove(app.url, s.id)} aria-current={current ? "step" : undefined}
                            className="w-full text-left group" title={current ? undefined : `Move to ${s.label}`}>
                      <span className="block h-1.5 rounded-full transition-colors" style={{ background: done ? "var(--accent)" : "rgba(238,233,223,0.12)" }} />
                      <span className="block mt-2 text-xs group-hover:underline underline-offset-4"
                            style={{ color: current ? "var(--text-primary)" : "var(--text-muted)", fontWeight: current ? 600 : 400 }}>{s.label}</span>
                    </button>
                  </li>
                );
              })}
            </ol>
            {closed && (
              <p className="mt-3 text-sm" style={{ color: app.status === "rejected" ? "var(--danger)" : "var(--text-secondary)" }}>
                {STATUS_LABEL[app.status]} on {shortDate(app.updated_at)}.
              </p>
            )}
            <div className="mt-5 flex flex-wrap gap-2">
              {closed ? (
                <button onClick={() => onMove(app.url, "to_apply")} className="h-9 px-4 rounded-lg text-sm font-semibold" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
                  Reopen
                </button>
              ) : (
                <>
                  {next && (
                    <button onClick={() => onMove(app.url, next.to)} className="h-9 px-4 rounded-lg text-sm font-semibold" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
                      {next.label}
                    </button>
                  )}
                  {app.status !== "to_apply" && (
                    <button onClick={() => onMove(app.url, "rejected")} className="h-9 px-3 rounded-lg border text-sm hover:bg-[var(--surface)]" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                      Rejected
                    </button>
                  )}
                  <button onClick={() => onMove(app.url, "withdrawn")} className="h-9 px-3 rounded-lg border text-sm hover:bg-[var(--surface)]" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                    {app.status === "offer" ? "Declined" : "Withdraw"}
                  </button>
                </>
              )}
            </div>
            {app.stale && (
              <p className="mt-4 text-sm" style={{ color: "var(--text-secondary)" }}>
                No answer for {app.days_in_status} days. A short, specific follow-up to the recruiter often gets one.
              </p>
            )}
          </section>

          {/* Links */}
          <section className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {posting && (
              <a href={posting} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1" style={{ color: "var(--accent)" }}>
                Open posting <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            )}
            {app.score != null && (
              <Link href={`/inbox?job=${encodeURIComponent(app.url)}`} style={{ color: "var(--text-secondary)" }}>
                Your fit: <span className="font-mono font-semibold" style={{ color: REC_COLOR[app.recommendation ?? ""] ?? "var(--text-primary)" }}>{app.score}</span> · read it in Opportunities →
              </Link>
            )}
          </section>

          {/* Notes */}
          <section>
            <div className="flex items-baseline justify-between">
              <p className={LABEL} style={LABEL_STYLE}>Notes</p>
              <span className="text-[11px]" style={{ color: noteState === "error" ? "var(--danger)" : "var(--text-muted)" }}>
                {noteState === "saving" ? "Saving…" : noteState === "saved" ? "Saved" : noteState === "error" ? "Couldn't save" : ""}
              </span>
            </div>
            <textarea value={notes} onChange={(e) => { setNotes(e.target.value); setNoteState("idle"); }} onBlur={saveNotes} rows={5}
                      placeholder="Recruiter's name, what they asked, what to prepare…"
                      className="mt-2 w-full rounded-lg border bg-transparent p-3 text-sm outline-none focus:border-[var(--accent)] resize-y"
                      style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
            <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>Saved when you click away.</p>
          </section>

          {/* What happened */}
          {events.length > 0 && (
            <section>
              <p className={LABEL} style={LABEL_STYLE}>History</p>
              <ol className="mt-3 relative border-l pl-5 space-y-4" style={{ borderColor: "var(--border)" }}>
                {events.map((e, i) => (
                  <li key={`${e.at}-${i}`} className="relative">
                    <span className="absolute -left-[25px] top-1.5 h-2 w-2 rounded-full" style={{ background: i === 0 ? "var(--accent)" : "var(--border-strong)" }} />
                    <p className="text-sm" style={{ color: i === 0 ? "var(--text-primary)" : "var(--text-secondary)" }}>{STATUS_LABEL[e.status] ?? e.status}</p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {new Date(e.at).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" })}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>

        <footer className="shrink-0 px-6 py-4 border-t flex items-center justify-between gap-4 text-xs" style={{ borderColor: "var(--border)" }}>
          <span style={{ color: "var(--text-muted)" }}>Tracked since {shortDate(app.created_at)}</span>
          {confirmRemove ? (
            <span className="flex items-center gap-3">
              <span style={{ color: "var(--text-secondary)" }}>Stop tracking it?</span>
              <button onClick={remove} className="underline underline-offset-4" style={{ color: "var(--danger)" }}>Yes, remove</button>
              <button onClick={() => setConfirmRemove(false)} style={{ color: "var(--text-muted)" }}>Cancel</button>
            </span>
          ) : (
            <button onClick={() => setConfirmRemove(true)} className="underline underline-offset-4" style={{ color: "var(--text-muted)" }}>Stop tracking</button>
          )}
        </footer>
      </div>
    </div>
  );
}
