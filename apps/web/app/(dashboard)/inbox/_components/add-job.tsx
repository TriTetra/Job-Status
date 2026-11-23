"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/shared/button";
import { ApiError } from "@/lib/api/client";
import { opportunitiesApi, type AddedJob } from "@/features/opportunities/api";

// Sites whose terms don't allow reading their pages (careeros/jobs/added.py NO_READING)
const PASTE_ONLY = /(^|\.)(linkedin|kariyer|indeed|glassdoor|kununu|xing)\./i;

/** The API's own message for a refused add (FastAPI: {"detail": "…"}), if it sent one. */
function reason(err: unknown): string | null {
  if (!(err instanceof ApiError) || err.status !== 422) return null;
  try {
    const detail = JSON.parse(err.body)?.detail;
    return typeof detail === "string" ? detail : null;
  } catch {
    return null;
  }
}

function hostOf(link: string): string {
  try {
    return new URL(link.includes("://") ? link : `https://${link}`).hostname;
  } catch {
    return "";
  }
}

/** "Add a job": a link (its page is read where the site allows it) or the posting's pasted text. */
export function AddJob({ onAdded, onClose }: { onAdded: (job: AddedJob) => void; onClose: () => void }) {
  const [link, setLink] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pasteOnly = PASTE_ONLY.test(hostOf(link));
  const [showText, setShowText] = useState(false);
  const textOpen = showText || pasteOnly || text.length > 0;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!link.trim() || busy) return;
    if (pasteOnly && text.trim().length < 200) {
      setError(`${hostOf(link)} doesn't allow its pages to be read: paste the posting text below.`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      onAdded(await opportunitiesApi.add(link.trim(), text.trim() || undefined));
    } catch (err) {
      const msg = reason(err);
      setError(msg ?? "That didn't work. Try again, or paste the posting text.");
      if (msg?.includes("paste")) setShowText(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="mt-5 pt-5 border-t max-w-[860px] shrink-0" style={{ borderColor: "var(--border)" }}>
      <p className="font-serif-display text-xl" style={{ color: "var(--text-primary)" }}>Add a job you found</p>
      <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
        Paste its link. Aplio reads the page where the site allows it, scores it for you and keeps it to you alone.
        For LinkedIn, Kariyer.net and similar sites, paste the posting text too.
      </p>

      <label className="mt-4 block text-xs" style={{ color: "var(--text-muted)" }} htmlFor="add-job-link">Link</label>
      <input
        id="add-job-link"
        value={link}
        onChange={(e) => setLink(e.target.value)}
        placeholder="https://…"
        autoFocus
        inputMode="url"
        className="w-full bg-transparent border-0 border-b outline-none py-1.5 text-[15px] focus:border-[var(--accent)]"
        style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}
      />

      {textOpen ? (
        <>
          <label className="mt-4 block text-xs" style={{ color: "var(--text-muted)" }} htmlFor="add-job-text">
            Posting text{pasteOnly ? "" : " (optional)"}: select the whole posting on the page, copy, paste
          </label>
          <textarea
            id="add-job-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={7}
            className="mt-1 w-full bg-transparent border rounded-md outline-none p-2.5 text-sm leading-relaxed focus:border-[var(--accent)] custom-scrollbar"
            style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </>
      ) : (
        <button type="button" onClick={() => setShowText(true)} className="mt-3 text-sm" style={{ color: "var(--accent)" }}>
          Paste the posting text instead
        </button>
      )}

      {error && <p className="mt-3 text-sm" role="alert" style={{ color: "var(--danger)" }}>{error}</p>}

      <div className="mt-4 flex items-center gap-3">
        <Button type="submit" size="md" disabled={busy || !link.trim()}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? "Reading and scoring…" : "Add and score"}
        </Button>
        <button type="button" onClick={onClose} className="text-sm" style={{ color: "var(--text-muted)" }}>Cancel</button>
        {busy && <span className="text-xs" style={{ color: "var(--text-muted)" }}>This takes up to half a minute.</span>}
      </div>
    </form>
  );
}
