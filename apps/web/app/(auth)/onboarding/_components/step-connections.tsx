"use client";

import { useState, useEffect, useCallback } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi } from "@/features/onboarding/api";
import {
  Github, Globe, Code, Gitlab, Dribbble, Figma, Database,
  GraduationCap, FlaskConical, Linkedin, Palette, Check, X,
  Fingerprint, BookOpen, Stethoscope, Building2, Home, PenTool, Layers,
} from "lucide-react";

interface Source {
  id: string; label: string; icon: string; category: string;
  status: string; connect_kind: string; oauth_provider: string | null;
  connected: boolean; suggested: boolean;
}

const ICONS: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  github: Github, globe: Globe, code: Code, gitlab: Gitlab,
  dribbble: Dribbble, figma: Figma, database: Database,
  graduation: GraduationCap, flask: FlaskConical, linkedin: Linkedin, behance: Palette,
  // multi-profession sources
  palette: Palette, fingerprint: Fingerprint, book: BookOpen, stethoscope: Stethoscope,
  building: Building2, home: Home, pen: PenTool, layers: Layers,
};

interface StepConnectionsProps {
  onComplete: () => void;
}

export function StepConnections({ onComplete }: StepConnectionsProps) {
  const [recommended, setRecommended] = useState<Source[]>([]);
  const [more, setMore] = useState<Source[]>([]);
  const [roleTitle, setRoleTitle] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [portfolioOpen, setPortfolioOpen] = useState(false);
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [crawling, setCrawling] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchSources = useCallback(() => {
    onboardingApi.getEvidenceSources()
      .then((data) => {
        // Bağlanabilir (available) olanlar her zaman üstte + suggested olanlar
        setRecommended(data.all.filter((s) => s.suggested || s.status === "available"));
        setMore(data.all.filter((s) => !s.suggested && s.status === "coming_soon"));
        setRoleTitle(data.role_title);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { fetchSources(); }, [fetchSources]);

  const handleConnect = (s: Source) => {
    if (s.connect_kind === "oauth" && s.oauth_provider) {
      window.location.href = `${apiBase}/api/oauth/${s.oauth_provider}/authorize`;
    } else if (s.connect_kind === "url") {
      setPortfolioOpen(true);
    }
  };

  const handleDisconnect = async (s: Source) => {
    try {
      if (s.oauth_provider === "github") await onboardingApi.disconnectGithub();
      else if (s.id === "portfolio") await onboardingApi.disconnectPortfolio();
      fetchSources();
    } catch (e) { console.error(e); }
  };

  const handleCrawl = async () => {
    if (!portfolioUrl) return;
    setCrawling(true);
    try {
      await onboardingApi.crawlPortfolio(portfolioUrl);
      setPortfolioOpen(false);
      setPortfolioUrl("");
      fetchSources();
    } catch (e) { console.error(e); }
    finally { setCrawling(false); }
  };

  const renderRecommended = (s: Source) => {
    const Icon = ICONS[s.icon] || Globe;
    const soon = s.status === "coming_soon";
    return (
      <div key={s.id}>
        <div
          className="flex items-center gap-3 p-2.5 rounded-lg border transition-colors"
          style={{
            borderColor: s.connected ? "var(--accent)" : "var(--border)",
            background: s.connected ? "rgba(255,177,98,0.05)" : "var(--surface)",
            opacity: soon ? 0.55 : 1,
          }}
        >
          <Icon className="h-5 w-5 shrink-0" style={{ color: s.connected ? "var(--accent)" : "var(--text-muted)" }} />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-[var(--text-primary)]">{s.label}</div>
            <div className="text-[11px] capitalize text-[var(--text-muted)]">{s.category}</div>
          </div>
          {soon ? (
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-[var(--border)] text-[var(--text-muted)]">Soon</span>
          ) : s.connected ? (
            <div className="flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full" style={{ background: "rgba(255,177,98,0.15)", color: "var(--accent)" }}>
                <Check className="h-3 w-3" strokeWidth={2.5} /> Connected
              </span>
              <button onClick={() => handleDisconnect(s)} className="p-1 hover:bg-[var(--surface-hover)] rounded" title="Disconnect">
                <X className="h-3.5 w-3.5 text-[var(--text-muted)]" />
              </button>
            </div>
          ) : (
            <button onClick={() => handleConnect(s)} className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              Connect
            </button>
          )}
        </div>
        {s.connect_kind === "url" && portfolioOpen && !s.connected && (
          <div className="flex gap-2 mt-1.5 ml-8">
            <input
              type="url"
              value={portfolioUrl}
              onChange={(e) => setPortfolioUrl(e.target.value)}
              placeholder="https://your-portfolio.com"
              className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none"
              style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              onKeyDown={(e) => e.key === "Enter" && handleCrawl()}
            />
            <button onClick={handleCrawl} disabled={!portfolioUrl || crawling} className="px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-40" style={{ background: "var(--accent)", color: "var(--accent-fg)" }}>
              {crawling ? "…" : "Add"}
            </button>
          </div>
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
          {roleTitle ? `Recommended for ${roleTitle}.` : "Link accounts to strengthen your signals."}
        </p>
      </div>

      {recommended.length > 0 && (
        <section>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">
            Recommended{roleTitle ? ` for ${roleTitle}` : ""}
          </label>
          <div className="space-y-1.5">{recommended.map(renderRecommended)}</div>
        </section>
      )}

      {more.length > 0 && (
        <section>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">
            More sources · coming soon
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {more.map((s) => {
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
