"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronsUpDown, LogOut, Plug, Settings, UserPlus } from "lucide-react";
import { cn, displayName } from "@/lib/utils";
import { signOut, useMe } from "@/features/auth/use-me";
import { settingsHref, type SectionId } from "@/features/settings/sections";

type Placement = "sidebar" | "sidebar-collapsed" | "topbar";

/** The one place for "you": who is signed in, Settings, connections, invites, sign out. */
export function AccountMenu({ placement }: { placement: Placement }) {
  const me = useMe();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const name = displayName(me?.first_name) || me?.email?.split("@")[0] || "You";
  const fullName = [displayName(me?.first_name), displayName(me?.last_name)].filter(Boolean).join(" ") || name;
  const initial = (me?.first_name?.[0] ?? me?.email?.[0] ?? "A").toUpperCase();

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const openSettings = (section: SectionId) => {
    setOpen(false);
    router.push(settingsHref(section), { scroll: false });
  };

  const avatar = (size: string) => (
    <span className={cn(size, "rounded-full flex items-center justify-center shrink-0 text-sm font-semibold")}
          style={{ background: "rgba(255,177,98,0.15)", color: "var(--accent)" }}>
      {initial}
    </span>
  );

  const items: Array<{ label: string; icon: typeof Settings; onClick: () => void; hint?: string }> = [
    { label: "Settings", icon: Settings, onClick: () => openSettings("profile"), hint: "Ctrl ," },
    { label: "Connections", icon: Plug, onClick: () => openSettings("connections") },
    ...(me?.is_admin ? [{ label: "Invite people", icon: UserPlus, onClick: () => openSettings("account") }] : []),
  ];

  const popover = cn(
    "absolute z-50 w-[248px] rounded-xl border py-1.5 menu-pop",
    placement === "sidebar" && "bottom-full left-0 right-0 w-auto mb-2",
    placement === "sidebar-collapsed" && "bottom-0 left-full ml-3",
    placement === "topbar" && "top-full right-0 mt-2",
  );

  return (
    <div ref={rootRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account: ${fullName}`}
        className={cn(
          "flex items-center gap-3 rounded-lg transition-colors",
          placement === "sidebar" && "w-full h-12 px-3 hover:bg-[var(--surface)]",
          placement === "sidebar-collapsed" && "h-10 w-10 mx-auto justify-center hover:bg-[var(--surface)]",
          placement === "topbar" && "h-9 w-9 justify-center hover:bg-[var(--surface)]",
          open && "bg-[var(--surface)]",
        )}
      >
        {avatar("h-8 w-8")}
        {placement === "sidebar" && (
          <>
            <span className="flex-1 min-w-0 text-left">
              <span className="block text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>{name}</span>
              <span className="block text-[11px] truncate" style={{ color: "var(--text-muted)" }}>{me?.email ?? ""}</span>
            </span>
            <ChevronsUpDown className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} strokeWidth={1.75} />
          </>
        )}
      </button>

      {open && (
        <div role="menu" aria-label="Account" className={popover}
             style={{ background: "var(--surface-elevated)", borderColor: "var(--border-strong)", boxShadow: "0 18px 48px rgba(0,0,0,0.45)" }}>
          <div className="px-3.5 pt-2 pb-2.5 flex items-center gap-3 border-b mb-1.5" style={{ borderColor: "var(--border)" }}>
            {avatar("h-9 w-9")}
            <span className="min-w-0">
              <span className="block text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>{fullName}</span>
              <span className="block text-xs truncate" style={{ color: "var(--text-muted)" }}>{me?.email}</span>
            </span>
          </div>
          {items.map((it) => (
            <button key={it.label} role="menuitem" onClick={it.onClick}
                    className="w-full flex items-center gap-3 h-9 px-3.5 text-sm text-left transition-colors hover:bg-[rgba(238,233,223,0.06)]"
                    style={{ color: "var(--text-secondary)" }}>
              <it.icon className="h-4 w-4 shrink-0" strokeWidth={1.75} style={{ color: "var(--text-muted)" }} />
              <span className="flex-1">{it.label}</span>
              {it.hint && <kbd className="text-[10px] font-mono" style={{ color: "var(--text-muted)" }}>{it.hint}</kbd>}
            </button>
          ))}
          <div className="h-px my-1.5" style={{ background: "var(--border)" }} />
          <button role="menuitem" onClick={() => void signOut()}
                  className="w-full flex items-center gap-3 h-9 px-3.5 text-sm text-left transition-colors hover:bg-[rgba(238,233,223,0.06)]"
                  style={{ color: "var(--text-secondary)" }}>
            <LogOut className="h-4 w-4 shrink-0" strokeWidth={1.75} style={{ color: "var(--text-muted)" }} />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
