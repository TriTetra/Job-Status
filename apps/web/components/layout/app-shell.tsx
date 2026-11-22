import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { CommandPalette } from "./command-palette";
import { type ReactNode } from "react";

/**
 * One viewport: sidebar + (topbar over a scrolling main). Pages that should fit the
 * screen (Briefing, Opportunities) use `h-full` and scroll inside their own columns.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-dvh overflow-hidden" style={{ background: "var(--background)", color: "var(--text-primary)" }}>
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <Topbar />
        <main id="main" className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden custom-scrollbar">
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
