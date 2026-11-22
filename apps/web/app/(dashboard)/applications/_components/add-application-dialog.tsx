"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { applicationsApi, type ApplicationStatus } from "@/features/applications/api";
import { STAGES } from "@/features/applications/format";

const FIELD = "w-full bg-transparent border-0 border-b outline-none py-1.5 text-sm focus:border-[var(--accent)] placeholder:text-[var(--text-muted)]";

/** Track a role you found outside Aplio. */
export function AddApplicationDialog({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [status, setStatus] = useState<ApplicationStatus>("applied");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef(onClose);
  const firstRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    closeRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    firstRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeRef.current();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const valid = /^https?:\/\/\S+$/i.test(url.trim()) && title.trim().length > 0;

  const submit = async () => {
    if (!valid) return;
    setSaving(true);
    setError(null);
    try {
      await applicationsApi.create({ url: url.trim(), title: title.trim(), company: company.trim() || undefined, status, notes: notes.trim() || undefined });
      onAdded();
    } catch {
      setError("Couldn't add it. Try again.");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 settings-scrim" onClick={onClose} aria-hidden="true" />
      <form role="dialog" aria-modal="true" aria-labelledby="add-title"
            onSubmit={(e) => { e.preventDefault(); submit(); }}
            className="settings-panel relative w-full max-w-[520px] rounded-2xl border p-7"
            style={{ background: "var(--background)", borderColor: "var(--border-strong)", boxShadow: "0 40px 120px rgba(0,0,0,0.55)" }}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="add-title" className="font-serif-display text-[26px] leading-tight" style={{ color: "var(--text-primary)" }}>Track an application</h2>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>A role you found outside Aplio.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="h-8 w-8 -mr-2 rounded-md flex items-center justify-center hover:bg-[var(--surface)]" style={{ color: "var(--text-muted)" }}>
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-6 space-y-5">
          <label className="block">
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>Link to the posting</span>
            <input ref={firstRef} type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" className={FIELD}
                   style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <label className="block">
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>Role</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Backend Engineer" className={FIELD}
                     style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
            </label>
            <label className="block">
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>Company</span>
              <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Optional" className={FIELD}
                     style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
            </label>
          </div>
          <fieldset>
            <legend className="text-xs" style={{ color: "var(--text-muted)" }}>Where it stands</legend>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {STAGES.map((s) => (
                <button key={s.id} type="button" onClick={() => setStatus(s.id)} aria-pressed={status === s.id}
                        className="px-3 py-1.5 rounded-full border text-xs transition-colors"
                        style={{ borderColor: status === s.id ? "var(--accent)" : "var(--border)", color: status === s.id ? "var(--accent)" : "var(--text-secondary)",
                                 background: status === s.id ? "rgba(255,177,98,0.06)" : "transparent" }}>
                  {s.label}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block">
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>Notes</span>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="Optional" className={`${FIELD} resize-none`}
                      style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
          </label>
        </div>

        {error && <p className="mt-4 text-xs" style={{ color: "var(--danger)" }}>{error}</p>}
        <div className="mt-7 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="h-9 px-4 rounded-lg text-sm" style={{ color: "var(--text-secondary)" }}>Cancel</button>
          <button type="submit" disabled={!valid || saving} className="h-9 px-5 rounded-lg text-sm font-semibold disabled:opacity-40"
                  style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
            {saving ? "Adding…" : "Add"}
          </button>
        </div>
      </form>
    </div>
  );
}
