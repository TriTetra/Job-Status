"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import { cn, displayName } from "@/lib/utils";
import { useMe } from "@/features/auth/use-me";
import { settingsApi } from "@/features/settings/api";
import { parseSection, SECTIONS, SETTINGS_PARAM, settingsHref, type SectionId } from "@/features/settings/sections";
import { ProfileTab } from "./profile-tab";
import { PreferencesTab } from "./preferences-tab";
import { ScoringTab } from "./scoring-tab";
import { AccountTab, ConnectionsTab } from "./account-tab";
import { toInitialProfile, type InitialProfile } from "./types";

/**
 * Settings as a dialog over whatever page you are on (?settings=<section>), so closing it
 * puts you back where you were. Ctrl/⌘ + , opens it from anywhere.
 */
export function SettingsDialogHost() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const section = parseSection(params.get(SETTINGS_PARAM));

  const go = useCallback(
    (next: SectionId | null) => {
      const q = new URLSearchParams(params.toString());
      if (next) q.set(SETTINGS_PARAM, next);
      else {
        q.delete(SETTINGS_PARAM);
        q.delete("github"); // the OAuth notice belongs to this visit only
      }
      const url = q.size ? `${pathname}?${q}` : pathname;
      if (next && section) router.replace(url, { scroll: false });
      else router.push(url, { scroll: false });
    },
    [params, pathname, router, section],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === ",") {
        e.preventDefault();
        router.push(settingsHref("profile"), { scroll: false });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  if (!section) return null;
  return <SettingsDialog section={section} onSelect={go} onClose={() => go(null)} />;
}

function SettingsDialog({ section, onSelect, onClose }: {
  section: SectionId;
  onSelect: (s: SectionId) => void;
  onClose: () => void;
}) {
  const me = useMe();
  const panelRef = useRef<HTMLDivElement>(null);
  const [profile, setProfile] = useState<InitialProfile | null | "error">(null);
  const current = SECTIONS.find((s) => s.id === section) ?? SECTIONS[0];
  const closeRef = useRef(onClose);
  useEffect(() => {
    closeRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    settingsApi.getIdentity().then((id) => setProfile(toInitialProfile(id))).catch(() => setProfile("error"));
  }, []);

  // Focus in, Escape out, focus back to whatever opened it
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeRef.current();
      if (e.key === "Tab" && panelRef.current) {
        const items = panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])');
        if (!items.length) return;
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      opener?.focus?.();
    };
  }, []);

  const name = [displayName(me?.first_name), displayName(me?.last_name)].filter(Boolean).join(" ") || me?.email?.split("@")[0] || "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center sm:p-6">
      <div className="absolute inset-0 settings-scrim" onClick={onClose} aria-hidden="true" />
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="settings-panel relative w-full h-full sm:h-[min(760px,calc(100dvh-48px))] sm:max-w-[1040px] sm:rounded-2xl border overflow-hidden flex flex-col sm:flex-row outline-none"
        style={{ background: "var(--background)", borderColor: "var(--border-strong)", boxShadow: "0 40px 120px rgba(0,0,0,0.55), 0 0 0 1px rgba(0,0,0,0.2)" }}
      >
        {/* Rail: the sections, and who you are */}
        <aside className="shrink-0 sm:w-[236px] flex flex-col border-b sm:border-b-0 sm:border-r"
               style={{ background: "rgba(44,59,77,0.35)", borderColor: "var(--border)" }}>
          <div className="flex items-center justify-between px-5 sm:px-6 pt-5 sm:pt-7 pb-3 sm:pb-5">
            <h2 id="settings-title" className="font-serif-display text-[22px] leading-none" style={{ color: "var(--text-primary)" }}>Settings</h2>
            <button onClick={onClose} aria-label="Close settings" className="sm:hidden h-8 w-8 -mr-1 rounded-md flex items-center justify-center hover:bg-[var(--surface)]" style={{ color: "var(--text-muted)" }}>
              <X className="h-4 w-4" />
            </button>
          </div>
          <nav aria-label="Settings sections" className="flex sm:flex-col gap-1 overflow-x-auto [scrollbar-width:none] px-3 pb-3 sm:pb-0 sm:flex-1">
            {SECTIONS.map((s) => {
              const active = s.id === section;
              return (
                <button
                  key={s.id}
                  onClick={() => onSelect(s.id)}
                  aria-current={active ? "page" : undefined}
                  className={cn("relative shrink-0 flex items-center gap-3 h-9 px-3 rounded-lg text-sm transition-colors whitespace-nowrap",
                    active ? "bg-[var(--surface)]" : "hover:bg-[rgba(44,59,77,0.6)]")}
                  style={{ color: active ? "var(--text-primary)" : "var(--text-secondary)", fontWeight: active ? 500 : 400 }}
                >
                  {active && <span className="hidden sm:block absolute left-0 top-1/2 -translate-y-1/2 h-4 w-[3px] rounded-r-full" style={{ background: "var(--accent)" }} />}
                  <s.icon className="h-4 w-4 shrink-0" strokeWidth={1.75} style={{ color: active ? "var(--accent)" : "var(--text-muted)" }} />
                  {s.label}
                </button>
              );
            })}
          </nav>
          {me && (
            <div className="hidden sm:flex items-center gap-3 px-6 py-5 border-t" style={{ borderColor: "var(--border)" }}>
              <span className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold shrink-0" style={{ background: "rgba(255,177,98,0.15)", color: "var(--accent)" }}>
                {(me.first_name?.[0] ?? me.email?.[0] ?? "A").toUpperCase()}
              </span>
              <span className="min-w-0">
                <span className="block text-sm truncate" style={{ color: "var(--text-primary)" }}>{name}</span>
                <span className="block text-xs truncate" style={{ color: "var(--text-muted)" }}>{me.email}</span>
              </span>
            </div>
          )}
        </aside>

        {/* The section */}
        <section className="flex-1 min-w-0 min-h-0 flex flex-col">
          <header className="shrink-0 flex items-start justify-between gap-6 px-6 sm:px-10 pt-6 sm:pt-8 pb-5 border-b" style={{ borderColor: "var(--border)" }}>
            <div className="min-w-0">
              <h3 className="font-serif-display text-[28px] leading-tight" style={{ color: "var(--text-primary)" }}>{current.label}</h3>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>{current.blurb}</p>
            </div>
            <button onClick={onClose} aria-label="Close settings" title="Close (Esc)"
                    className="hidden sm:flex h-9 w-9 -mr-2 rounded-lg items-center justify-center transition-colors hover:bg-[var(--surface)]" style={{ color: "var(--text-muted)" }}>
              <X className="h-[18px] w-[18px]" />
            </button>
          </header>

          {/* Every section stays mounted, so edits survive switching sections */}
          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-6 sm:px-10 pt-6">
            <div hidden={section !== "profile"}>
              {profile === null ? (
                <p className="text-sm py-8" style={{ color: "var(--text-muted)" }}>Loading…</p>
              ) : (
                <ProfileTab initial={profile === "error" ? null : profile} />
              )}
            </div>
            <div hidden={section !== "preferences"}><PreferencesTab /></div>
            <div hidden={section !== "scoring"}><ScoringTab /></div>
            <div hidden={section !== "connections"}><ConnectionsTab /></div>
            <div hidden={section !== "account"}><AccountTab /></div>
            <div className="h-6" />
          </div>
        </section>
      </div>
    </div>
  );
}
