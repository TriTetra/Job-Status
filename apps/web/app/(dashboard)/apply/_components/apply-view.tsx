"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Check, Copy, Loader2, RefreshCw } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { opportunitiesApi } from "@/features/opportunities/api";
import { SKIP_REASONS, type SkipReason } from "@/features/opportunities/format";
import { SOURCE_LABEL, applyApi, type Kit, type KitQuestion, type QueueItem } from "@/features/apply/api";
import { cn, safeHttpUrl } from "@/lib/utils";

const LABEL = "text-[11px] uppercase tracking-[0.08em]";
const LABEL_STYLE = { color: "var(--text-muted)", fontFamily: "var(--font-display)" } as const;

const pct = (p: number | null | undefined) => (typeof p === "number" ? `${(p * 100).toFixed(p < 0.1 ? 1 : 0)}%` : null);

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button" aria-label="Copy"
            onClick={() => navigator.clipboard?.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1500); })}
            className="shrink-0 h-7 px-2 rounded-md border text-xs inline-flex items-center gap-1 hover:bg-[var(--surface-hover)]"
            style={{ borderColor: "var(--border)", color: done ? "var(--success)" : "var(--text-secondary)" }}>
      {done ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {done ? "Copied" : "Copy"}
    </button>
  );
}

/** One form question: what to put in it, where that comes from, and anything to watch. */
function QuestionRow({ q }: { q: KitQuestion }) {
  const [text, setText] = useState(q.suggested ?? "");
  const yours = q.source === "you" || q.source === "llm";
  const draft = q.source === "draft";
  return (
    <li className="py-3 border-b last:border-b-0" style={{ borderColor: "var(--border)" }}>
      <p className="text-sm" style={{ color: "var(--text-primary)" }}>
        {q.label}{q.required && <span style={{ color: "var(--danger)" }}> *</span>}
      </p>
      <p className="text-[11px] mt-0.5" style={{ color: yours ? "var(--accent)" : "var(--text-muted)" }}>
        {SOURCE_LABEL[q.source]}{q.note ? ` · ${q.note}` : ""}
      </p>
      {!yours && q.kind !== "file" && (
        draft ? (
          <div className="mt-2 flex items-start gap-2">
            <textarea value={text} onChange={(e) => setText(e.target.value)} rows={Math.min(8, Math.max(3, Math.ceil(text.length / 90)))}
                      className="flex-1 min-w-0 rounded-lg border bg-transparent p-2.5 text-sm leading-relaxed outline-none focus:border-[var(--accent)]"
                      style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }} />
            <CopyButton text={text} />
          </div>
        ) : q.suggested ? (
          <div className="mt-1.5 flex items-center gap-2">
            <p className="flex-1 min-w-0 text-sm truncate" style={{ color: "var(--text-secondary)" }}>{q.suggested}</p>
            <CopyButton text={q.suggested} />
          </div>
        ) : null
      )}
      {q.kind === "file" && q.suggested && (
        <p className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>{q.suggested}</p>
      )}
    </li>
  );
}

function KitPanel({ item, kit, preparing, onPrepare, onApplied, onSkip, busy }: {
  item: QueueItem; kit: Kit | null; preparing: boolean; busy: boolean;
  onPrepare: (refresh: boolean) => void; onApplied: () => void; onSkip: (r: SkipReason[]) => void;
}) {
  const [note, setNote] = useState(kit?.cover_note ?? "");
  const [skipOpen, setSkipOpen] = useState(false);
  const applyUrl = safeHttpUrl(kit?.apply_url ?? item.apply_url);
  const chance = pct(item.p_interview);
  return (
    <div className="h-full flex flex-col min-h-0">
      <header className="px-8 pt-7 pb-5 border-b shrink-0" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-start gap-4">
          <CompanyLogo name={item.company} companyKey={item.company_key} jobUrl={item.url} size={52} />
          <div className="min-w-0 flex-1">
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{item.company}{item.location ? ` · ${item.location}` : ""}</p>
            <h2 className="font-serif-display text-[26px] leading-tight mt-0.5" style={{ color: "var(--text-primary)" }}>{item.title}</h2>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Score {Math.round(item.score ?? 0)}{chance ? ` · ${chance} chance of an interview` : ""}
              {kit ? ` · ${kit.form === "greenhouse" ? "the company's own form" : "the questions most forms ask"}` : ""}
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {applyUrl && (
            <a href={applyUrl} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-1.5 rounded-lg h-10 px-4 text-sm font-semibold"
               style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              Open the application form <ArrowUpRight className="h-4 w-4" />
            </a>
          )}
          <button type="button" onClick={onApplied} disabled={busy}
                  className="h-10 px-4 rounded-lg border text-sm disabled:opacity-50 hover:bg-[var(--surface-hover)]"
                  style={{ borderColor: "var(--border)", color: "var(--text-primary)" }}>
            I submitted it
          </button>
          <button type="button" onClick={() => setSkipOpen((v) => !v)} disabled={busy}
                  className="h-10 px-4 rounded-lg border text-sm disabled:opacity-50 hover:bg-[var(--surface-hover)]"
                  style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
            Not for me
          </button>
        </div>
        {skipOpen && (
          <div role="menu" aria-label="Why is it not for you?" className="menu-pop mt-2 flex flex-wrap gap-1.5">
            {SKIP_REASONS.map((r) => (
              <button key={r.id} role="menuitem" type="button" onClick={() => { setSkipOpen(false); onSkip([r.id]); }}
                      className="text-xs px-2.5 py-1 rounded-full border hover:bg-[var(--surface-hover)]"
                      style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                {r.label}
              </button>
            ))}
            <button role="menuitem" type="button" onClick={() => { setSkipOpen(false); onSkip([]); }}
                    className="text-xs px-2.5 py-1" style={{ color: "var(--text-muted)" }}>Just skip</button>
          </div>
        )}
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-8 py-6">
        {!kit ? (
          <div className="max-w-md">
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Aplio reads the form, fills in what it knows about you, and drafts the free-text answers from your evidence.
              You review everything and submit it yourself.
            </p>
            <button type="button" onClick={() => onPrepare(false)} disabled={preparing}
                    className="mt-4 inline-flex items-center gap-1.5 h-10 px-4 rounded-lg text-sm font-semibold disabled:opacity-60"
                    style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              {preparing ? <><Loader2 className="h-4 w-4 animate-spin" /> Preparing…</> : "Prepare this application"}
            </button>
          </div>
        ) : (
          <div className="grid xl:grid-cols-[minmax(0,1fr)_280px] gap-x-10 gap-y-8">
            <section className="min-w-0">
              {kit.warnings.length > 0 && (
                <div className="mb-5 rounded-lg border p-3 text-sm space-y-1" style={{ borderColor: "rgba(230,168,23,0.45)", color: "var(--text-secondary)" }}>
                  {kit.warnings.map((w) => <p key={w}>⚠ {w}</p>)}
                </div>
              )}
              <p className={LABEL} style={LABEL_STYLE}>The form · {kit.questions.length} questions</p>
              <ul className="mt-1">
                {kit.questions.map((q) => <QuestionRow key={q.id} q={q} />)}
              </ul>
            </section>
            <aside className="space-y-7">
              <section>
                <p className={LABEL} style={LABEL_STYLE}>CV to send</p>
                {kit.cv ? (
                  <p className="mt-2 text-sm" style={{ color: "var(--text-primary)" }}>{kit.cv.filename} <span style={{ color: "var(--text-muted)" }}>· version {kit.cv.version}</span></p>
                ) : (
                  <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
                    No CV in Aplio yet. <Link href="/apply?settings=account" scroll={false} style={{ color: "var(--accent)" }}>Upload it</Link> so each application records the CV you sent.
                  </p>
                )}
                {kit.matched?.length > 0 && (
                  <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    Make sure it shows: {kit.matched.slice(0, 5).join(", ")}.
                  </p>
                )}
              </section>
              <section>
                <div className="flex items-baseline justify-between">
                  <p className={LABEL} style={LABEL_STYLE}>Short note</p>
                  {note && <CopyButton text={note} />}
                </div>
                {kit.cover_note ? (
                  <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={9}
                            className="mt-2 w-full rounded-lg border bg-transparent p-2.5 text-sm leading-relaxed outline-none focus:border-[var(--accent)]"
                            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }} />
                ) : (
                  <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
                    {kit.ai_policy ? "Not drafted: this company sets rules on AI in applications." : "Nothing drafted: write a few lines yourself if the form asks."}
                  </p>
                )}
              </section>
              <section className="text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                <p>Aplio prepared this; you submit it. Nothing is sent for you, and legal agreements are always yours to read.</p>
                <button type="button" onClick={() => onPrepare(true)} disabled={preparing}
                        className="mt-2 inline-flex items-center gap-1 underline underline-offset-4 disabled:opacity-50">
                  {preparing ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />} Prepare again
                </button>
              </section>
            </aside>
          </div>
        )}
      </div>
    </div>
  );
}

/** Ready to apply: today's few best jobs, each prepared so you only review and submit. */
export function ApplyView() {
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [preparing, setPreparing] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    applyApi.queue().then((r) => setItems(r.items)).catch(() => setError(true));
  }, []);

  const current = items?.find((i) => i.url === selected) ?? items?.[0] ?? null;

  const prepare = async (url: string, refresh: boolean) => {
    setPreparing(url);
    setMessage(null);
    try {
      const { kit } = await applyApi.prepare(url, refresh);
      setItems((xs) => xs?.map((x) => (x.url === url ? { ...x, kit, ready: true } : x)) ?? xs);
    } catch {
      setMessage("Couldn't prepare it right now. Try again in a minute.");
    } finally {
      setPreparing(null);
    }
  };

  const decide = async (url: string, status: "applied" | "skipped", reasons: SkipReason[] = []) => {
    setBusy(true);
    setMessage(null);
    try {
      await opportunitiesApi.decide(url, status, { reasons, surface: "queue" });
      setItems((xs) => xs?.filter((x) => x.url !== url) ?? xs);
      setSelected(null);
      setMessage(status === "applied" ? "Recorded as applied. It's on your Applications board." : "Skipped.");
    } catch {
      setMessage("That didn't save. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5">
      <header className="shrink-0 max-w-[860px]">
        <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Ready to apply</h1>
        <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Today&apos;s best jobs to send, one per company: open, not ruled out, from employers that look reliable.
          Each comes prepared: the form&apos;s questions with answers from your profile, drafts from your evidence, and the CV to send.
          You review and submit; Aplio never sends anything for you.
        </p>
        {message && <p className="mt-2 text-sm" role="status" style={{ color: "var(--accent)" }}>{message}</p>}
      </header>

      {error ? (
        <p className="mt-10 text-sm" style={{ color: "var(--danger)" }}>The queue couldn&apos;t be loaded. Try again.</p>
      ) : items === null ? (
        <div className="mt-6 space-y-2 max-w-[360px]">{[0, 1, 2].map((i) => <div key={i} className="h-16 rounded-lg skeleton-shimmer" />)}</div>
      ) : items.length === 0 ? (
        <div className="flex-1 py-20 text-center max-w-md mx-auto">
          <p className="font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>Nothing to send today.</p>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            No open match clears the bar right now. <Link href="/inbox" style={{ color: "var(--accent)" }}>See all opportunities</Link> or widen your countries in Settings.
          </p>
        </div>
      ) : (
        <div className="mt-5 lg:flex-1 lg:min-h-0 grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] gap-6">
          <ul className="max-h-[50vh] lg:max-h-none lg:min-h-0 overflow-y-auto custom-scrollbar space-y-1 pr-2" aria-label="Ready to apply">
            {items.map((it, i) => {
              const active = current?.url === it.url;
              return (
                <li key={it.url}>
                  <button type="button" onClick={() => setSelected(it.url)} aria-current={active ? "true" : undefined}
                          className={cn("relative w-full text-left grid grid-cols-[1.5rem_2.5rem_minmax(0,1fr)] gap-x-3 px-3 py-3 rounded-lg transition-colors",
                            active ? "bg-[var(--surface)]" : "hover:bg-[rgba(44,59,77,0.5)]")}>
                    {active && <span className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" style={{ background: "var(--accent)" }} />}
                    <span className="font-serif-display text-lg leading-none pt-2.5 tabular-nums" style={{ color: "var(--text-muted)" }}>{i + 1}</span>
                    <CompanyLogo name={it.company} companyKey={it.company_key} jobUrl={it.url} size={40} />
                    <span className="min-w-0">
                      <span className="block text-sm font-medium leading-snug line-clamp-2" style={{ color: "var(--text-primary)" }}>{it.title}</span>
                      <span className="block text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>{it.company} · {Math.round(it.score ?? 0)}</span>
                      <span className="block text-[11px] mt-0.5" style={{ color: it.kit ? "var(--success)" : "var(--text-muted)" }}>
                        {preparing === it.url ? "Preparing…" : it.kit ? "Prepared" : "Not prepared yet"}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="rounded-2xl border overflow-hidden lg:min-h-0 h-[80vh] lg:h-auto" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            {current && (
              <KitPanel key={`${current.url}:${current.kit?.created_at ?? "none"}`} item={current} kit={current.kit}
                        preparing={preparing === current.url} busy={busy}
                        onPrepare={(refresh) => prepare(current.url, refresh)}
                        onApplied={() => decide(current.url, "applied")}
                        onSkip={(r) => decide(current.url, "skipped", r)} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
