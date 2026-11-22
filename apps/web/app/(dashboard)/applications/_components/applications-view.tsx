"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { CompanyLogo } from "@/components/shared/company-logo";
import { cn } from "@/lib/utils";
import { applicationsApi, CLOSED_STATUSES, type Application, type ApplicationStatus } from "@/features/applications/api";
import { ageLine, companyOf, REC_COLOR, STAGES, STATUS_LABEL, shortDate } from "@/features/applications/format";
import { ApplicationDrawer } from "./application-drawer";
import { AddApplicationDialog } from "./add-application-dialog";

type View = "board" | "closed";

function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

/** The sentence at the top: where your search stands, in one breath. */
function lead(apps: Application[]): string {
  const by = (s: ApplicationStatus) => apps.filter((a) => a.status === s);
  const [queued, waiting, talking, offers] = [by("to_apply"), by("applied"), by("interview"), by("offer")];
  const stale = waiting.filter((a) => a.stale).length;
  const live = waiting.length + talking.length + offers.length;
  if (!apps.length) return "";
  const parts: string[] = [];
  if (live) {
    const bits = [
      offers.length ? plural(offers.length, "offer") : "",
      talking.length ? plural(talking.length, "interview") : "",
      waiting.length ? `${waiting.length} waiting to hear back${stale ? ` (${stale} for over two weeks)` : ""}` : "",
    ].filter(Boolean);
    parts.push(`You're in ${plural(live, "process", "processes")}: ${bits.join(", ")}.`);
  } else {
    parts.push("Nothing sent yet.");
  }
  if (queued.length) parts.push(`${plural(queued.length, "role")} shortlisted to apply.`);
  return parts.join(" ");
}

export function ApplicationsView({ initialApps }: { initialApps: Application[] }) {
  const [apps, setApps] = useState<Application[]>(initialApps);
  const [view, setView] = useState<View>("board");
  const [query, setQuery] = useState("");
  const [openUrl, setOpenUrl] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<ApplicationStatus | null>(null);

  const reload = useCallback(async () => {
    try {
      setApps(await applicationsApi.list());
    } catch (err) {
      console.error("[applications] refresh failed:", err);
    }
  }, []);

  const move = useCallback(async (url: string, status: ApplicationStatus) => {
    setApps((prev) => prev.map((a) => (a.url === url ? { ...a, status, days_in_status: 0, stale: false } : a)));
    try {
      await applicationsApi.move(url, status);
    } finally {
      reload();
    }
  }, [reload]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? apps.filter((a) => `${a.title} ${companyOf(a)}`.toLowerCase().includes(q)) : apps;
  }, [apps, query]);
  const closed = shown.filter((a) => CLOSED_STATUSES.includes(a.status));
  const opened = apps.find((a) => a.url === openUrl) ?? null;

  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1680px] mx-auto px-6 lg:px-8 pt-7 pb-5">
      <div className="shrink-0 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-[860px]">
          <h1 className="font-serif-display text-[34px] leading-none" style={{ color: "var(--text-primary)" }}>Applications</h1>
          <p className="mt-3 text-[15px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {apps.length ? lead(apps) : "Nothing tracked yet."}
          </p>
        </div>
        <button onClick={() => setAdding(true)}
                className="inline-flex items-center gap-2 h-9 px-4 rounded-lg border text-sm transition-colors hover:bg-[var(--surface)]"
                style={{ borderColor: "var(--border-strong)", color: "var(--text-primary)" }}>
          <Plus className="h-4 w-4" /> Add application
        </button>
      </div>

      <div className="mt-5 shrink-0 flex flex-wrap items-center gap-x-6 gap-y-3 border-b pb-3" style={{ borderColor: "var(--border)" }}>
        <nav className="flex gap-5" aria-label="Views">
          {([["board", "Pipeline", apps.length - closed.length], ["closed", "Closed", apps.filter((a) => CLOSED_STATUSES.includes(a.status)).length]] as const).map(([id, label, n]) => (
            <button key={id} onClick={() => setView(id)} aria-current={view === id ? "page" : undefined} className="text-sm"
                    style={{ color: view === id ? "var(--text-primary)" : "var(--text-muted)", fontWeight: view === id ? 600 : 400 }}>
              {label} <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>{n}</span>
            </button>
          ))}
        </nav>
        <label className="ml-auto flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
          <Search className="h-4 w-4" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Company or title" aria-label="Search applications"
                 className="w-44 bg-transparent border-0 border-b outline-none py-1 text-sm focus:border-[var(--accent)]"
                 style={{ borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </label>
      </div>

      {apps.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
          <p className="font-serif-display text-2xl" style={{ color: "var(--text-primary)" }}>Your pipeline starts in Opportunities</p>
          <p className="mt-2 max-w-md text-sm" style={{ color: "var(--text-secondary)" }}>
            Shortlist a role or mark it applied there and it shows up here. Found one somewhere else? Add it yourself.
          </p>
          <div className="mt-5 flex gap-4 text-sm">
            <Link href="/inbox" style={{ color: "var(--accent)" }}>Go to Opportunities →</Link>
            <button onClick={() => setAdding(true)} style={{ color: "var(--text-secondary)" }}>Add one</button>
          </div>
        </div>
      ) : view === "board" ? (
        <div className="mt-4 lg:flex-1 lg:min-h-0 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 lg:auto-rows-[minmax(0,1fr)] gap-4">
          {STAGES.map((stage) => {
            const cards = shown.filter((a) => a.status === stage.id);
            const target = dropTarget === stage.id && dragging != null;
            return (
              <section
                key={stage.id}
                aria-label={stage.label}
                onDragOver={(e) => {
                  if (!dragging) return;
                  e.preventDefault();
                  setDropTarget(stage.id);
                }}
                onDragLeave={() => setDropTarget((t) => (t === stage.id ? null : t))}
                onDrop={(e) => {
                  e.preventDefault();
                  const url = e.dataTransfer.getData("text/plain");
                  setDropTarget(null);
                  setDragging(null);
                  const app = apps.find((a) => a.url === url);
                  if (app && app.status !== stage.id) move(url, stage.id);
                }}
                className="min-h-[200px] lg:min-h-0 flex flex-col rounded-2xl border transition-colors"
                style={{
                  background: target ? "rgba(255,177,98,0.06)" : "rgba(44,59,77,0.22)",
                  borderColor: target ? "var(--accent)" : "var(--border)",
                }}
              >
                <header className="shrink-0 px-4 pt-4 pb-3 flex items-baseline justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{stage.label}</h2>
                    <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>{stage.hint}</p>
                  </div>
                  <span className="font-serif-display text-2xl tabular-nums" style={{ color: cards.length ? "var(--text-primary)" : "var(--text-muted)" }}>{cards.length}</span>
                </header>
                <ul className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-2 pb-2 space-y-2">
                  {cards.map((a) => (
                    <li key={a.url}>
                      <Card app={a} dragging={dragging === a.url}
                            onOpen={() => setOpenUrl(a.url)}
                            onNext={stage.next ? () => move(a.url, stage.next!.to) : undefined}
                            nextLabel={stage.next ? STATUS_LABEL[stage.next.to] : undefined}
                            onDragStart={(e) => {
                              e.dataTransfer.setData("text/plain", a.url);
                              e.dataTransfer.effectAllowed = "move";
                              setDragging(a.url);
                            }}
                            onDragEnd={() => {
                              setDragging(null);
                              setDropTarget(null);
                            }} />
                    </li>
                  ))}
                  {cards.length === 0 && (
                    <li className="px-3 py-6 text-center text-xs" style={{ color: "var(--text-muted)" }}>
                      {dragging ? "Drop here" : stage.id === "to_apply" ? "Shortlist roles in Opportunities" : "Nothing here yet"}
                    </li>
                  )}
                </ul>
              </section>
            );
          })}
        </div>
      ) : (
        <div className="mt-2 lg:flex-1 lg:min-h-0 overflow-y-auto custom-scrollbar">
          {closed.length === 0 ? (
            <p className="py-16 text-center text-sm" style={{ color: "var(--text-muted)" }}>Nothing closed. Rejections and withdrawals land here.</p>
          ) : (
            <ul className="max-w-[980px]">
              {closed.map((a) => (
                <li key={a.url}>
                  <button onClick={() => setOpenUrl(a.url)}
                          className="w-full text-left grid grid-cols-[2.25rem_minmax(0,1fr)_auto] items-center gap-x-4 py-3 border-b -mx-3 px-3 rounded-md hover:bg-[rgba(44,59,77,0.5)] transition-colors"
                          style={{ borderColor: "var(--border)" }}>
                    <CompanyLogo name={companyOf(a)} companyKey={a.company_key} size={36} />
                    <span className="min-w-0">
                      <span className="block text-sm truncate" style={{ color: "var(--text-primary)" }}>{a.title}</span>
                      <span className="block text-xs truncate" style={{ color: "var(--text-muted)" }}>{companyOf(a)}</span>
                    </span>
                    <span className="text-xs text-right" style={{ color: a.status === "rejected" ? "var(--danger)" : "var(--text-muted)" }}>
                      {STATUS_LABEL[a.status]} · {shortDate(a.updated_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {opened && (
        <ApplicationDrawer key={opened.url} app={opened} onClose={() => setOpenUrl(null)} onMove={move}
                           onChanged={reload} onRemoved={() => { setOpenUrl(null); reload(); }} />
      )}
      {adding && <AddApplicationDialog onClose={() => setAdding(false)} onAdded={() => { setAdding(false); reload(); }} />}
    </div>
  );
}

function Card({ app, dragging, onOpen, onNext, nextLabel, onDragStart, onDragEnd }: {
  app: Application;
  dragging: boolean;
  onOpen: () => void;
  onNext?: () => void;
  nextLabel?: string;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
}) {
  const age = ageLine(app);
  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={cn("group rounded-xl border transition-all cursor-grab active:cursor-grabbing", dragging && "opacity-40")}
      style={{ background: "var(--surface)", borderColor: app.stale ? "rgba(201,106,90,0.5)" : "var(--border)" }}
    >
      <button onClick={onOpen} className="w-full text-left p-3 pb-2 grid grid-cols-[2rem_minmax(0,1fr)_auto] gap-x-3">
        <CompanyLogo name={companyOf(app)} companyKey={app.company_key} size={32} className="mt-0.5" />
        <span className="min-w-0">
          <span className="block text-sm leading-snug line-clamp-2" style={{ color: "var(--text-primary)" }}>{app.title}</span>
          <span className="block text-xs mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>
            {companyOf(app)}{app.remote ? " · Remote" : app.location ? ` · ${app.location}` : ""}
          </span>
        </span>
        {app.score != null && (
          <span className="font-mono text-sm font-semibold tabular-nums" style={{ color: REC_COLOR[app.recommendation ?? ""] ?? "var(--text-muted)" }}>
            {app.score}
          </span>
        )}
      </button>
      <div className="px-3 pb-3 flex items-center justify-between gap-2 text-[11px]">
        <span className="truncate" style={{ color: app.stale ? "var(--danger)" : "var(--text-muted)" }}>
          {app.stale ? `${age} · follow up?` : age}{app.posting_closed ? " · posting closed" : ""}
        </span>
        {onNext && nextLabel && (
          <button onClick={onNext} title={`Move to ${nextLabel}`}
                  className="shrink-0 px-2 py-0.5 rounded-md border transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)]"
                  style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
            → {nextLabel}
          </button>
        )}
      </div>
    </div>
  );
}
