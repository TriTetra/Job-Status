"use client";

import Link from "next/link";
import { useState } from "react";
import { dismissTodo } from "@/features/briefing/client";
import type { TodoFact } from "@/features/briefing";

/** Concrete things to do, each with one action; "Not now" hides it for a week. */
export function BriefingTodos({ todos }: { todos: TodoFact[] }) {
  const [hidden, setHidden] = useState<string[]>([]);
  const visible = todos.filter((t) => !hidden.includes(t.key));

  const dismiss = (key: string) => {
    setHidden((h) => [...h, key]);
    dismissTodo(key).catch(() => setHidden((h) => h.filter((k) => k !== key)));
  };

  return (
    <section className="lg:min-h-0 flex flex-col">
      <p className="text-[11px] uppercase tracking-[0.08em] shrink-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>
        To do{visible.length ? ` · ${visible.length}` : ""}
      </p>
      {visible.length === 0 ? (
        <p className="mt-4 font-editorial text-lg" style={{ color: "var(--text-secondary)" }}>Nothing waiting on you. Enjoy the quiet.</p>
      ) : (
        <ol className="mt-3 lg:min-h-0 lg:overflow-y-auto custom-scrollbar -mr-3 pr-3">
          {visible.map((t, i) => (
            <li key={t.key} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-x-3 py-4 [@media(max-height:820px)]:py-3 border-b last:border-b-0" style={{ borderColor: "var(--border)" }}>
              <span className="font-mono text-sm pt-0.5" style={{ color: "var(--accent)" }}>{String(i + 1).padStart(2, "0")}</span>
              <div className="min-w-0">
                <p className="text-[15px] font-medium leading-snug" style={{ color: "var(--text-primary)" }}>{t.title}</p>
                <p className="mt-1 text-sm leading-relaxed line-clamp-2 [@media(max-height:820px)]:line-clamp-1" title={t.detail} style={{ color: "var(--text-muted)" }}>{t.detail}</p>
                <div className="mt-1.5 flex items-center gap-5 text-sm">
                  {t.external ? (
                    <a href={t.cta_href} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)" }}>{t.cta_label} ↗</a>
                  ) : (
                    <Link href={t.cta_href} style={{ color: "var(--accent)" }}>{t.cta_label} →</Link>
                  )}
                  <button onClick={() => dismiss(t.key)} style={{ color: "var(--text-muted)" }}>Not now</button>
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
