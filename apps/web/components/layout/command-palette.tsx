"use client";

import { useEffect } from "react";
import { Command } from "cmdk";
import { useUIStore } from "@/lib/store";
import { ALL_NAV_ITEMS } from "@/lib/nav-items";
import { useRouter } from "next/navigation";
import { FileText, Plus, Zap } from "lucide-react";

const QUICK_ACTIONS = [
  { label: "Generate Resume", icon: FileText, href: "/resume" },
  { label: "Add Application", icon: Plus, href: "/applications" },
  { label: "Scan for Jobs", icon: Zap, href: "/inbox" },
];

export function CommandPalette() {
  const { commandOpen, setCommandOpen } = useUIStore();
  const router = useRouter();

  useEffect(() => {
    if (!commandOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setCommandOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [commandOpen, setCommandOpen]);

  const handleSelect = (href: string) => {
    setCommandOpen(false);
    router.push(href);
  };

  if (!commandOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0"
        style={{ background: "rgba(27,38,50,0.7)", backdropFilter: "blur(4px)" }}
        onClick={() => setCommandOpen(false)}
      />
      <div className="relative flex items-start justify-center pt-[15vh] px-4">
        <Command
          className="w-full max-w-[560px] rounded-xl overflow-hidden"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border-strong)",
            boxShadow: "0 24px 48px rgba(0,0,0,0.4)",
          }}
        >
          <Command.Input
            autoFocus
            placeholder="Search pages, actions, companies..."
            className="w-full h-14 px-5 bg-transparent outline-none text-[15px] border-b"
            style={{
              color: "var(--text-primary)",
              borderColor: "var(--border)",
            }}
          />

          <Command.List className="max-h-[380px] overflow-y-auto p-2">
            <Command.Empty
              className="py-8 text-center text-sm"
              style={{ color: "var(--text-muted)" }}
            >
              No results found.
            </Command.Empty>

            <div
              className="text-[11px] font-medium tracking-wider uppercase px-3 py-2"
              style={{ color: "var(--text-muted)" }}
            >
              Quick Actions
            </div>
            {QUICK_ACTIONS.map((action) => (
              <Command.Item
                key={action.label}
                value={action.label}
                onSelect={() => handleSelect(action.href)}
                className="flex items-center gap-3 h-10 px-3 rounded-lg text-sm cursor-pointer transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                <action.icon className="h-4 w-4" style={{ color: "var(--accent)" }} strokeWidth={1.75} />
                <span>{action.label}</span>
              </Command.Item>
            ))}

            <div
              className="text-[11px] font-medium tracking-wider uppercase px-3 pt-4 pb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Pages
            </div>
            {ALL_NAV_ITEMS.filter((i) => !i.comingSoon).map((item) => (
              <Command.Item
                key={item.href}
                value={item.label}
                onSelect={() => handleSelect(item.href)}
                className="flex items-center gap-3 h-10 px-3 rounded-lg text-sm cursor-pointer transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                <item.icon className="h-4 w-4" style={{ color: "var(--text-muted)" }} strokeWidth={1.75} />
                <span className="flex-1">{item.label}</span>
                {item.badge !== undefined && (
                  <span className="text-[11px] tabular-nums" style={{ color: "var(--text-muted)" }}>
                    {item.badge}
                  </span>
                )}
              </Command.Item>
            ))}
          </Command.List>

          <div
            className="h-10 px-4 border-t flex items-center gap-4 text-[11px]"
            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
          >
            {[["↑↓", "navigate"], ["↵", "select"], ["esc", "close"]].map(([key, label]) => (
              <span key={key} className="flex items-center gap-1">
                <kbd
                  className="px-1.5 py-0.5 rounded border font-mono"
                  style={{ background: "var(--background)", borderColor: "var(--border)" }}
                >
                  {key}
                </kbd>
                {label}
              </span>
            ))}
          </div>
        </Command>
      </div>
    </div>
  );
}
