"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { Plus, Search, ExternalLink, Loader2, X, Check } from "lucide-react";
import {
  applicationsApi,
  type Application,
  type ApplicationStatus,
} from "@/features/applications/api";

const COLUMNS: { id: ApplicationStatus; label: string; hint: string }[] = [
  { id: "to_apply",  label: "To Apply",  hint: "Queued" },
  { id: "applied",   label: "Applied",   hint: "In review" },
  { id: "interview", label: "Interview", hint: "In progress" },
  { id: "offer",     label: "Offer",     hint: "Decision time" },
];

const TERMINAL: ApplicationStatus[] = ["rejected", "withdrawn"];

function hostFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "—";
  }
}

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [formUrl, setFormUrl] = useState("");
  const [formTitle, setFormTitle] = useState("");
  const [formCompany, setFormCompany] = useState("");
  const [formStatus, setFormStatus] = useState<ApplicationStatus>("to_apply");
  const [formNotes, setFormNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setApps(await applicationsApi.list());
    } catch {
      setApps([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!formUrl || !formTitle) return;
    setSaving(true);
    try {
      await applicationsApi.create({
        url: formUrl,
        title: formTitle,
        company: formCompany || undefined,
        status: formStatus,
      });
      setModalOpen(false);
      setFormUrl("");
      setFormTitle("");
      setFormCompany("");
      setFormNotes("");
      setFormStatus("to_apply");
      load();
    } catch {
      /* sessiz */
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (url: string, newStatus: ApplicationStatus) => {
    // Optimistic update
    setApps((prev) => prev.map((a) => (a.url === url ? { ...a, status: newStatus } : a)));
    try {
      await applicationsApi.update(url, { status: newStatus });
    } catch {
      load(); // Rollback on error
    }
  };

  const filtered = useMemo(() => {
    if (!search) return apps;
    const q = search.toLowerCase();
    return apps.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        (a.company ?? "").toLowerCase().includes(q) ||
        a.url.toLowerCase().includes(q)
    );
  }, [apps, search]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    apps.forEach((a) => {
      c[a.status] = (c[a.status] ?? 0) + 1;
    });
    return c;
  }, [apps]);

  const activePipeline = apps.filter((a) => !TERMINAL.includes(a.status));
  const archived = filtered.filter((a) => TERMINAL.includes(a.status));

  return (
    <div className="wide-container px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <NarrativeText size="2xl" weight="semibold" as="h1" className="mb-1">
            Applications
          </NarrativeText>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {apps.length} tracked · {activePipeline.length} active ·{" "}
            {counts.offer ?? 0} offer{counts.offer === 1 ? "" : "s"}
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Add application
        </Button>
      </div>

      {/* Search */}
      <div className="mb-8 max-w-sm relative">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
          strokeWidth={1.75}
          style={{ color: "var(--text-muted)" }}
        />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search applications..."
          className="w-full h-9 pl-9 pr-3 rounded-lg text-sm outline-none transition-colors"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text-primary)",
          }}
        />
      </div>

      {loading ? (
        <div className="surface p-12 text-center">
          <Loader2
            className="h-5 w-5 animate-spin mx-auto mb-3"
            style={{ color: "var(--text-muted)" }}
          />
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Loading pipeline…
          </p>
        </div>
      ) : apps.length === 0 ? (
        <div className="surface p-12 text-center">
          <NarrativeText size="lg" weight="medium" className="mb-2">
            No applications yet
          </NarrativeText>
          <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
            Track your first application to start building your pipeline.
          </p>
          <Button variant="outline" onClick={() => setModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Add first application
          </Button>
        </div>
      ) : (
        <>
          {/* Pipeline Board — 4 hairline-separated columns */}
          <div
            className="grid grid-cols-1 md:grid-cols-4 border-t border-b"
            style={{ borderColor: "var(--border)" }}
          >
            {COLUMNS.map((col, i) => {
              const colApps = filtered.filter((a) => a.status === col.id);
              return (
                <div
                  key={col.id}
                  className="py-6 px-4 border-b md:border-b-0"
                  style={{
                    borderRight: i < COLUMNS.length - 1 ? "1px solid var(--border)" : "none",
                    borderBottomColor: "var(--border)",
                  }}
                >
                  {/* Column header */}
                  <div className="flex items-baseline justify-between mb-4">
                    <div>
                      <div
                        className="text-[11px] font-semibold tracking-wider uppercase"
                        style={{
                          color: "var(--text-muted)",
                          fontFamily: "var(--font-display)",
                        }}
                      >
                        {col.label}
                      </div>
                      <div
                        className="text-[10px] mt-0.5"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {col.hint}
                      </div>
                    </div>
                    <span
                      className="text-sm font-semibold tabular-nums"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {colApps.length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="space-y-2">
                    {colApps.map((app) => (
                      <ApplicationCard
                        key={app.url}
                        app={app}
                        onStatusChange={handleStatusChange}
                      />
                    ))}
                    {colApps.length === 0 && (
                      <div
                        className="py-8 text-center text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        —
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Closed (rejected / withdrawn) */}
          {archived.length > 0 && (
            <div
              className="mt-8 pt-6 border-t"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-baseline justify-between mb-4">
                <div
                  className="text-[11px] font-semibold tracking-wider uppercase"
                  style={{ color: "var(--text-muted)" }}
                >
                  Closed
                </div>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {archived.length}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {archived.map((app) => (
                  <ApplicationCard
                    key={app.url}
                    app={app}
                    onStatusChange={handleStatusChange}
                    compact
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Add modal */}
      {modalOpen && (
        <AddApplicationModal
          url={formUrl}
          title={formTitle}
          company={formCompany}
          status={formStatus}
          notes={formNotes}
          setUrl={setFormUrl}
          setTitle={setFormTitle}
          setCompany={setFormCompany}
          setStatus={setFormStatus}
          setNotes={setFormNotes}
          saving={saving}
          onClose={() => setModalOpen(false)}
          onSubmit={handleCreate}
        />
      )}
    </div>
  );
}

/* ─── Application Card ──────────────────────────────────────────────────── */

const STATUS_TRANSITIONS: Record<
  ApplicationStatus,
  { to: ApplicationStatus; label: string }[]
> = {
  to_apply:  [{ to: "applied", label: "Mark applied" }, { to: "withdrawn", label: "Withdraw" }],
  applied:   [{ to: "interview", label: "Got interview" }, { to: "rejected", label: "Rejected" }, { to: "withdrawn", label: "Withdraw" }],
  interview: [{ to: "offer", label: "Got offer" }, { to: "rejected", label: "Rejected" }, { to: "withdrawn", label: "Withdraw" }],
  offer:     [{ to: "applied", label: "Declined" }],
  rejected:  [{ to: "to_apply", label: "Reopen" }],
  withdrawn: [{ to: "to_apply", label: "Reopen" }],
};

function ApplicationCard({
  app,
  onStatusChange,
  compact = false,
}: {
  app: Application;
  onStatusChange: (url: string, status: ApplicationStatus) => void;
  compact?: boolean;
}) {
  const displayCompany = app.company || hostFromUrl(app.url);
  const transitions = STATUS_TRANSITIONS[app.status] ?? [];

  return (
    <div
      className="rounded-lg border transition-colors group"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className={compact ? "p-3" : "p-4"}>
        {/* Title + link */}
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="min-w-0 flex-1">
            <div
              className={`font-medium truncate ${compact ? "text-xs" : "text-sm"}`}
              style={{ color: "var(--text-primary)" }}
            >
              {app.title}
            </div>
            <div
              className="text-[11px] truncate mt-0.5"
              style={{ color: "var(--text-muted)" }}
            >
              {displayCompany} · {formatDate(app.applied_at)}
            </div>
          </div>
          <a
            href={app.url}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ExternalLink
              className="h-3.5 w-3.5"
              strokeWidth={1.75}
              style={{ color: "var(--text-muted)" }}
            />
          </a>
        </div>

        {/* Status transition buttons */}
        {transitions.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {transitions.map((t) => (
              <button
                key={t.to}
                onClick={() => onStatusChange(app.url, t.to)}
                className="text-[10px] px-2 py-0.5 rounded border transition-colors cursor-pointer"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
                  (e.currentTarget as HTMLElement).style.color = "var(--accent)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                  (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Add Application Modal ─────────────────────────────────────────────── */

function AddApplicationModal({
  url, title, company, status, notes,
  setUrl, setTitle, setCompany, setStatus, setNotes,
  saving, onClose, onSubmit,
}: {
  url: string; title: string; company: string;
  status: ApplicationStatus; notes: string;
  setUrl: (v: string) => void;
  setTitle: (v: string) => void;
  setCompany: (v: string) => void;
  setStatus: (v: ApplicationStatus) => void;
  setNotes: (v: string) => void;
  saving: boolean;
  onClose: () => void;
  onSubmit: () => void;
}) {
  const isValid = url.trim().length > 0 && title.trim().length > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{ background: "rgba(27,38,50,0.75)", backdropFilter: "blur(4px)" }}
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className="relative w-full max-w-md rounded-xl border p-6"
        style={{
          background: "var(--surface)",
          borderColor: "var(--border-strong)",
          boxShadow: "0 24px 48px rgba(0,0,0,0.4)",
        }}
      >
        <div className="flex items-start justify-between mb-5">
          <div>
            <NarrativeText size="lg" weight="semibold">
              Track an application
            </NarrativeText>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
              Add a role you&apos;ve applied to or are planning to apply.
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-7 w-7 flex items-center justify-center rounded-md transition-colors hover:bg-surface-hover cursor-pointer"
          >
            <X className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
          </button>
        </div>

        <div className="space-y-4">
          {/* URL */}
          <div>
            <label
              className="block text-[11px] font-semibold tracking-wider uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Job URL *
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          {/* Title */}
          <div>
            <label
              className="block text-[11px] font-semibold tracking-wider uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Role title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Senior Backend Engineer"
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          {/* Company */}
          <div>
            <label
              className="block text-[11px] font-semibold tracking-wider uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Company
            </label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Stripe"
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          {/* Status */}
          <div>
            <label
              className="block text-[11px] font-semibold tracking-wider uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Status
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {(["to_apply", "applied", "interview", "offer"] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatus(s)}
                  className="px-2 py-1.5 rounded-lg border text-[10px] font-semibold capitalize transition-all cursor-pointer"
                  style={{
                    borderColor: status === s ? "var(--accent)" : "var(--border)",
                    background: status === s ? "rgba(255,177,98,0.06)" : "transparent",
                    color: status === s ? "var(--accent)" : "var(--text-secondary)",
                  }}
                >
                  {s.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label
              className="block text-[11px] font-semibold tracking-wider uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Referral, interview date, etc."
              className="w-full px-3 py-2 rounded-lg border text-sm outline-none resize-none"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
        </div>

        <div
          className="flex items-center justify-end gap-2 mt-6 pt-5 border-t"
          style={{ borderColor: "var(--border)" }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm transition-colors cursor-pointer"
            style={{ color: "var(--text-secondary)" }}
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={!isValid || saving}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            style={{ background: "var(--accent)", color: "var(--accent-fg)" }}
          >
            {saving ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" />Saving…</>
            ) : (
              <><Check className="h-3.5 w-3.5" />Add</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
