"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import { NAV_GROUPS, type NavItem } from "@/lib/nav-items";
import { useUIStore } from "@/lib/store";
import { AplioLogo } from "@/components/shared/aplio-logo";
import { PanelLeftClose, PanelLeft } from "lucide-react";

function NavItemRow({
  item,
  active,
  collapsed,
}: {
  item: NavItem;
  active: boolean;
  collapsed: boolean;
}) {
  const inner = (
    <>
      <item.icon
        className={cn(
          "h-[18px] w-[18px] shrink-0 transition-colors duration-150",
          active ? "text-[var(--accent)]" : "text-[var(--text-secondary)]"
        )}
        strokeWidth={1.75}
      />
      {!collapsed && (
        <>
          <span
            className={cn(
              "flex-1 truncate text-sm transition-colors duration-150",
              active ? "text-[var(--text-primary)] font-medium" : "text-[var(--text-secondary)]"
            )}
          >
            {item.label}
          </span>
          {item.comingSoon && (
            <span className="text-[10px] font-medium tracking-wider uppercase text-[var(--text-muted)]">
              Soon
            </span>
          )}
          {item.badge !== undefined && !item.comingSoon && (
            <span
              className={cn(
                "text-[11px] font-medium tabular-nums px-1.5 py-0.5 rounded-md",
                active
                  ? "bg-[var(--accent)]/20 text-[var(--accent)]"
                  : "bg-[var(--surface-hover)] text-[var(--text-secondary)]"
              )}
            >
              {item.badge}
            </span>
          )}
        </>
      )}
    </>
  );

  const base = cn(
    "relative flex items-center gap-3 h-9 rounded-lg px-3 transition-all duration-150",
    collapsed && "justify-center px-0 w-10 mx-auto",
    item.disabled || item.comingSoon
      ? "opacity-40 cursor-not-allowed"
      : "cursor-pointer hover:bg-[var(--surface)]",
    active && "bg-[var(--surface)]"
  );

  if (item.disabled || item.comingSoon) {
    return <div className={base}>{inner}</div>;
  }

  return (
    <Link href={item.href} className={base} title={collapsed ? item.label : undefined}>
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-[var(--accent)] rounded-r-full" />
      )}
      {inner}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { user } = useUser();
  const displayName = user?.firstName ?? user?.username ?? "You";
  const displayRole = user?.unsafeMetadata?.role as string | undefined;
  const initials = (user?.firstName?.[0] ?? user?.username?.[0] ?? "A").toUpperCase();

  return (
    <aside
      className={cn(
        "hidden lg:flex flex-col h-screen sticky top-0 border-r transition-all duration-200",
        sidebarCollapsed ? "w-[72px]" : "w-[260px]"
      )}
      style={{
        background: "var(--background)",
        borderColor: "var(--border)",
      }}
    >
      {/* Logo */}
      <div
        className="h-16 flex items-center justify-between px-4 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <Link href="/" className="flex items-center gap-2 min-w-0">
          <AplioLogo
            variant={sidebarCollapsed ? "icon" : "wordmark"}
            size="sm"
          />
        </Link>
        {!sidebarCollapsed && (
          <button
            onClick={toggleSidebar}
            className="h-7 w-7 rounded-md flex items-center justify-center transition-colors hover:bg-[var(--surface)]"
            style={{ color: "var(--text-muted)" }}
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" strokeWidth={1.75} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-5 px-3 space-y-5">
        {sidebarCollapsed && (
          <button
            onClick={toggleSidebar}
            className="w-full h-9 flex items-center justify-center rounded-lg transition-colors hover:bg-[var(--surface)]"
            style={{ color: "var(--text-muted)" }}
            aria-label="Expand sidebar"
          >
            <PanelLeft className="h-[18px] w-[18px]" strokeWidth={1.75} />
          </button>
        )}
        {NAV_GROUPS.map((group) => (
          <div key={group.title}>
            {!sidebarCollapsed && (
              <div
                className="text-[11px] font-medium tracking-wider uppercase px-3 mb-1.5"
                style={{ color: "var(--text-muted)" }}
              >
                {group.title}
              </div>
            )}
            {sidebarCollapsed && (
              <div className="h-px mx-2 mb-2" style={{ background: "var(--border)" }} />
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active =
                  item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <NavItemRow
                    key={item.href}
                    item={item}
                    active={active}
                    collapsed={sidebarCollapsed}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User */}
      <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
        <div
          className={cn(
            "flex items-center gap-3 h-12 rounded-lg px-3 hover:bg-[var(--surface)] transition-colors cursor-pointer",
            sidebarCollapsed && "justify-center px-0"
          )}
        >
          <div
            className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
            style={{ background: "rgba(255,177,98,0.15)" }}
          >
            <span className="text-sm font-semibold" style={{ color: "var(--accent)" }}>{initials}</span>
          </div>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {displayName}
              </div>
              {displayRole && (
                <div className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                  {displayRole}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
