"use client";

import { Search, Bell, Command, LogOut } from "lucide-react";
import { signOut, useMe } from "@/features/auth/use-me";
import { useUIStore } from "@/lib/store";
import { usePathname } from "next/navigation";
import { NAV_GROUPS } from "@/lib/nav-items";
import { useEffect } from "react";

/** Initials + sign out (replaces the hosted account widget). */
function AccountButton() {
  const me = useMe();
  const initial = (me?.first_name?.[0] ?? me?.email?.[0] ?? "·").toUpperCase();
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold"
        style={{ background: "var(--surface)", color: "var(--text-secondary)" }}
        title={me?.email}
      >
        {initial}
      </span>
      <button
        onClick={() => void signOut()}
        className="h-8 w-8 rounded-md flex items-center justify-center transition-colors"
        style={{ color: "var(--text-muted)" }}
        aria-label="Sign out"
        title="Sign out"
      >
        <LogOut className="h-[16px] w-[16px]" strokeWidth={1.75} />
      </button>
    </div>
  );
}

function Breadcrumb() {
  const pathname = usePathname();
  let currentLabel = "Briefing";
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)) {
        currentLabel = item.label;
        break;
      }
    }
  }
  return (
    <div className="flex items-center gap-2 text-sm">
      <span style={{ color: "var(--text-muted)" }}>Aplio</span>
      <span style={{ color: "var(--text-muted)" }}>/</span>
      <span className="font-medium" style={{ color: "var(--text-primary)" }}>
        {currentLabel}
      </span>
    </div>
  );
}

export function Topbar() {
  const { setCommandOpen } = useUIStore();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setCommandOpen]);

  return (
    <header
      className="sticky top-0 z-30 h-16 border-b"
      style={{
        background: "rgba(27,38,50,0.85)",
        backdropFilter: "blur(16px)",
        borderColor: "var(--border)",
      }}
    >
      <div className="h-full flex items-center justify-between px-6 lg:px-8 gap-4">
        <div className="hidden md:block">
          <Breadcrumb />
        </div>

        <button
          onClick={() => setCommandOpen(true)}
          className="flex-1 max-w-md h-9 flex items-center gap-2 px-3 rounded-lg border transition-colors"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "var(--surface-hover)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "var(--surface)")
          }
        >
          <Search
            className="h-4 w-4 shrink-0"
            style={{ color: "var(--text-muted)" }}
            strokeWidth={1.75}
          />
          <span
            className="text-sm flex-1 text-left"
            style={{ color: "var(--text-muted)" }}
          >
            Search anything...
          </span>
          <kbd
            className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border text-[11px] font-mono"
            style={{
              background: "var(--background)",
              borderColor: "var(--border)",
              color: "var(--text-muted)",
            }}
          >
            <Command className="h-3 w-3" strokeWidth={2} />K
          </kbd>
        </button>

        <div className="flex items-center gap-2">
          <button
            className="relative h-9 w-9 flex items-center justify-center rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "var(--surface)")
            }
            onMouseLeave={(e) => (e.currentTarget.style.background = "")}
            aria-label="Notifications"
          >
            <Bell className="h-[18px] w-[18px]" strokeWidth={1.75} />
            <span
              className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full"
              style={{
                background: "var(--accent)",
                outline: "2px solid var(--background)",
              }}
            />
          </button>

          <AccountButton />
        </div>
      </div>
    </header>
  );
}
