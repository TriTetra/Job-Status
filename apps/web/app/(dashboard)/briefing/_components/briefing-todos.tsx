"use client";

import Link from "next/link";
import { useState } from "react";
import { SectionLabel } from "@/components/shared/narrative-section";
import { dismissTodo } from "@/features/briefing/client";
import type { TodoFact } from "@/features/briefing";
import { Movement } from "./movement";

/** Concrete things to do, each with one action; "Not now" hides it for a week. */
export function BriefingTodos({ todos }: { todos: TodoFact[] }) {
  const [hidden, setHidden] = useState<string[]>([]);
  const visible = todos.filter((t) => !hidden.includes(t.key));
  if (visible.length === 0) return null;

  const dismiss = (key: string) => {
    setHidden((h) => [...h, key]);
    dismissTodo(key).catch(() => setHidden((h) => h.filter((k) => k !== key)));
  };

  return (
    <Movement delay={280}>
      <SectionLabel>To do</SectionLabel>
      <ol className="divide-y" style={{ borderColor: "var(--border)" }}>
        {visible.map((t, i) => (
          <li key={t.key} className="grid grid-cols-[2.5rem_minmax(0,1fr)] md:grid-cols-[2.5rem_minmax(0,1fr)_auto] gap-x-3 gap-y-2 py-5 first:pt-0"
              style={{ borderColor: "var(--border)" }}>
            <span className="font-mono text-sm pt-1" style={{ color: "var(--accent)" }}>{String(i + 1).padStart(2, "0")}</span>
            <div>
              <p className="text-base font-medium" style={{ color: "var(--text-primary)" }}>{t.title}</p>
              <p className="mt-1 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{t.detail}</p>
            </div>
            <div className="col-start-2 md:col-start-3 flex items-center gap-5 text-sm md:pt-1 whitespace-nowrap">
              <button onClick={() => dismiss(t.key)} style={{ color: "var(--text-muted)" }}>Not now</button>
              {t.external ? (
                <a href={t.cta_href} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)" }}>
                  {t.cta_label} ↗
                </a>
              ) : (
                <Link href={t.cta_href} style={{ color: "var(--accent)" }}>{t.cta_label} →</Link>
              )}
            </div>
          </li>
        ))}
      </ol>
    </Movement>
  );
}
