"use client";

import type { InputHTMLAttributes, ReactNode } from "react";
import { Check } from "lucide-react";
import { SectionLabel } from "@/components/shared/narrative-section";

/** Hairline ile ayrılan bölüm */
export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="pt-8 mt-8 first:pt-0 first:mt-0 border-t border-[var(--border)] first:border-t-0">
      <SectionLabel>{title}</SectionLabel>
      <div className="mt-2">{children}</div>
    </section>
  );
}

/** Sol label+hint, sağ kontrol — düz satır, hairline ayraç. */
export function Row({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="py-4 grid grid-cols-1 md:grid-cols-[220px_1fr] gap-1.5 md:gap-8 border-b border-[var(--border)] last:border-b-0">
      <div>
        <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {label}
        </div>
        {hint && (
          <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {hint}
          </div>
        )}
      </div>
      <div className="md:pt-0.5">{children}</div>
    </div>
  );
}

/** NN/g: checkbox = küçük kare, dikey liste, pozitif label. */
export function CheckRow({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="w-full py-3.5 flex items-start gap-3 text-left border-b border-[var(--border)] last:border-b-0 cursor-pointer"
    >
      <span
        className="mt-0.5 h-4 w-4 shrink-0 rounded-[3px] border flex items-center justify-center transition-colors"
        style={
          checked
            ? { background: "var(--accent)", borderColor: "var(--accent)" }
            : { borderColor: "var(--border-strong)" }
        }
      >
        {checked && (
          <Check className="h-3 w-3" strokeWidth={3} style={{ color: "var(--accent-fg)" }} />
        )}
      </span>
      <span>
        <span className="block text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {label}
        </span>
        {hint && (
          <span className="block text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {hint}
          </span>
        )}
      </span>
    </button>
  );
}

/** NN/g: mutually-exclusive seçenek = radio (küçük daire). */
export function RadioRow({
  checked,
  onSelect,
  label,
  hint,
}: {
  checked: boolean;
  onSelect: () => void;
  label: string;
  hint?: string;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={checked}
      onClick={onSelect}
      className="w-full py-3.5 flex items-start gap-3 text-left border-b border-[var(--border)] last:border-b-0 cursor-pointer"
    >
      <span
        className="mt-0.5 h-4 w-4 shrink-0 rounded-full border flex items-center justify-center transition-colors"
        style={{ borderColor: checked ? "var(--accent)" : "var(--border-strong)" }}
      >
        {checked && (
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--accent)" }} />
        )}
      </span>
      <span>
        <span className="block text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {label}
        </span>
        {hint && (
          <span className="block text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {hint}
          </span>
        )}
      </span>
    </button>
  );
}

/** Onboarding pill dili — tek/çok seçim chip'leri. */
export function Pill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="px-3 py-1.5 rounded-full border text-xs font-medium transition-all cursor-pointer"
      style={{
        borderColor: active ? "var(--accent)" : "var(--border)",
        background: active ? "rgba(255,177,98,0.05)" : "transparent",
        color: active ? "var(--accent)" : "var(--text-secondary)",
      }}
    >
      {children}
    </button>
  );
}

/** Kutusuz input — sadece alt hairline. */
export function UnderlineInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={[
        "w-full md:max-w-[260px] bg-transparent border-0 border-b border-[var(--border)]",
        "focus:border-[var(--accent)] outline-none py-1 text-sm transition-colors",
        "placeholder:text-[var(--text-muted)]",
        props.className ?? "",
      ].join(" ")}
      style={{ color: "var(--text-primary)" }}
    />
  );
}

/** Tek save noktası — NN/g: ayarlar confirm ile uygulanır. */
export function SaveBar({
  onSave,
  saving,
  saved,
  disabled,
}: {
  onSave: () => void;
  saving: boolean;
  saved: boolean;
  disabled?: boolean;
}) {
  return (
    <div className="pt-8 mt-8 border-t border-[var(--border)] flex items-center justify-end gap-4">
      {saved && (
        <span className="text-xs" style={{ color: "var(--success)" }}>
          Saved
        </span>
      )}
      <button
        type="button"
        onClick={onSave}
        disabled={disabled || saving}
        className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        style={{ background: "var(--accent)", color: "var(--accent-fg)" }}
      >
        {saving ? "Saving…" : "Save changes"}
      </button>
    </div>
  );
}
