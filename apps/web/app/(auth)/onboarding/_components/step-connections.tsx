"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi } from "@/features/onboarding/api";
import { githubNotice, NOTICE_COLOR } from "@/features/onboarding/connect-messages";
import { connectsByInput, SOURCE_INPUT, useSourceConnect } from "@/features/onboarding/use-source-connect";
import type { EvidenceSourceRow } from "@/features/onboarding/types";
import {
  Github, Globe, Code, Gitlab, Dribbble, Figma, Database,
  GraduationCap, FlaskConical, Linkedin, Palette, Check, X,
  Fingerprint, BookOpen, Stethoscope, Building2, Home, PenTool, Layers,
} from "lucide-react";

const ICONS: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  github: Github, globe: Globe, code: Code, gitlab: Gitlab,
  dribbble: Dribbble, figma: Figma, database: Database,
  graduation: GraduationCap, flask: FlaskConical, linkedin: Linkedin, behance: Palette,
  // multi-profession sources
  palette: Palette, fingerprint: Fingerprint, book: BookOpen, stethoscope: Stethoscope,
  building: Building2, home: Home, pen: PenTool, layers: Layers,
};

const LABEL = "block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]";

interface StepConnectionsProps {
  onComplete: () => void;
}

export function StepConnections({ onComplete }: StepConnectionsProps) {
  const [sources, setSources] = useState<EvidenceSourceRow[]>([]);
  const [roleTitle, setRoleTitle] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const oauthNotice = githubNotice(useSearchParams().get("github"));

  const fetchSources = useCallback(() => {
    onboardingApi.getEvidenceSources()
      .then((data) => {
        setSources(data.all);
        setRoleTitle(data.role_title);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { fetchSources(); }, [fetchSources]);

  const c = useSourceConnect(fetchSources, "onboarding");

  // Recommended for the role first, then everything else that works today, then what's coming
  const recommended = sources.filter((s) => s.suggested);
  const available = sources.filter((s) => !s.suggested && s.status === "available");
  const soon = sources.filter((s) => !s.suggested && s.status !== "available");

  const renderRow = (s: EvidenceSourceRow) => {
    const Icon = ICONS[s.icon] || Globe;
    const comingSoon = s.status !== "available";
    const open = c.openId === s.id;
    const busy = c.busyId === s.id;
    const notice = c.notices[s.id];
    return (
      <div key={s.id}>
        <div
          className="flex items-center gap-3 p-2.5 rounded-lg border transition-colors"
          style={{
            borderColor: s.connected ? "var(--accent)" : "var(--border)",
            background: s.connected ? "rgba(255,177,98,0.05)" : "var(--surface)",
            opacity: comingSoon ? 0.55 : 1,
          }}
        >
          <Icon className="h-5 w-5 shrink-0" style={{ color: s.connected ? "var(--accent)" : "var(--text-muted)" }} />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-[var(--text-primary)]">{s.label}</div>
            <div className="text-[11px] text-[var(--text-muted)] truncate">
              {s.connected && s.handle ? s.handle : SOURCE_INPUT[s.id]?.hint ?? s.category}
            </div>
          </div>
          {comingSoon ? (
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-[var(--border)] text-[var(--text-muted)]">Soon</span>
          ) : s.connected ? (
            <div className="flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full" style={{ background: "rgba(255,177,98,0.15)", color: "var(--accent)" }}>
                <Check className="h-3 w-3" strokeWidth={2.5} /> Connected
              </span>
              <button onClick={() => c.disconnect(s)} disabled={busy} className="p-1 hover:bg-[var(--surface-hover)] rounded" title="Disconnect" aria-label={`Disconnect ${s.label}`}>
                <X className="h-3.5 w-3.5 text-[var(--text-muted)]" />
              </button>
            </div>
          ) : !open ? (
            <button onClick={() => c.start(s)} className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              Connect
            </button>
          ) : null}
        </div>

        {open && connectsByInput(s) && (
          <div className="flex gap-2 mt-1.5 ml-8">
            <input
              autoFocus
              value={c.value}
              onChange={(e) => c.setValue(e.target.value)}
              placeholder={SOURCE_INPUT[s.id]?.placeholder ?? "Username or profile link"}
              aria-label={`${s.label} username or link`}
              className="flex-1 min-w-0 px-3 py-1.5 rounded-lg border text-sm outline-none focus:border-[var(--accent)]"
              style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              onKeyDown={(e) => {
                if (e.key === "Enter") c.submit(s);
                if (e.key === "Escape") c.cancel();
              }}
            />
            <button onClick={() => c.submit(s)} disabled={!c.value.trim() || busy} className="px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-40" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              {busy ? "Reading…" : "Add"}
            </button>
            <button onClick={c.cancel} className="px-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
              Cancel
            </button>
          </div>
        )}
        {notice && (
          <p className="text-xs mt-1.5 ml-8" role={notice.tone === "error" ? "alert" : "status"} style={{ color: NOTICE_COLOR[notice.tone] }}>
            {notice.text}
          </p>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="flex items-center justify-center py-24"><div className="animate-spin h-6 w-6 border-2 border-[var(--accent)] border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="space-y-4">
      <div>
        <NarrativeText size="xl" weight="semibold">Connect your proof sources.</NarrativeText>
        <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
          Paste a username or profile link — we read only what&apos;s public. {roleTitle ? `Recommended for ${roleTitle}.` : ""}
        </p>
        {oauthNotice && (
          <p className="text-xs mt-2" role={oauthNotice.tone === "error" ? "alert" : "status"} style={{ color: NOTICE_COLOR[oauthNotice.tone] }}>
            {oauthNotice.text}
          </p>
        )}
      </div>

      {recommended.length > 0 && (
        <section>
          <label className={LABEL}>Recommended{roleTitle ? ` for ${roleTitle}` : ""}</label>
          <div className="space-y-1.5">{recommended.map(renderRow)}</div>
        </section>
      )}

      {available.length > 0 && (
        <section>
          <label className={LABEL}>Also available</label>
          <div className="space-y-1.5">{available.map(renderRow)}</div>
        </section>
      )}

      {soon.length > 0 && (
        <section>
          <label className={LABEL}>More sources · coming soon</label>
          <div className="grid grid-cols-2 gap-1.5">
            {soon.map((s) => {
              const Icon = ICONS[s.icon] || Globe;
              return (
                <div key={s.id} className="flex items-center gap-2 px-2.5 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] opacity-55">
                  <Icon className="h-4 w-4 shrink-0 text-[var(--text-muted)]" />
                  <span className="text-xs text-[var(--text-secondary)] truncate">{s.label}</span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      <button onClick={onComplete} className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all" style={{ background: "var(--accent)", color: "var(--accent-fg)", cursor: "pointer" }}>
        Continue
      </button>
    </div>
  );
}
