"use client";

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Search, X, Check } from "lucide-react";

interface Option {
  id: string;
  label: string;
}

interface SearchableMultiSelectProps {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
  maxSelections?: number;
  minSelections?: number;
  placeholder?: string;
}

export function SearchableMultiSelect({
  options,
  selected,
  onChange,
  maxSelections = 5,
  minSelections = 0,
  placeholder = "Search...",
}: SearchableMultiSelectProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(query.toLowerCase())
  );

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      if (selected.length > minSelections) {
        onChange(selected.filter((s) => s !== id));
      }
    } else {
      if (selected.length < maxSelections) {
        onChange([...selected, id]);
      }
    }
  };

  const removeSelected = (id: string) => {
    if (selected.length > minSelections) {
      onChange(selected.filter((s) => s !== id));
    }
  };

  const selectedOptions = options.filter((o) => selected.includes(o.id));
  const atMax = selected.length >= maxSelections;

  return (
    <div ref={containerRef} className="relative">
      {/* Selected chips + search input */}
      <div
        onClick={() => setIsOpen(true)}
        className={cn(
          "min-h-[44px] p-2 flex flex-wrap gap-1.5 items-center cursor-text",
          "bg-[var(--surface)] border rounded-md transition-colors",
          isOpen ? "border-[var(--border-strong)]" : "border-[var(--border)] hover:bg-[var(--surface-hover)]"
        )}
      >
        {selectedOptions.map((option) => (
          <span
            key={option.id}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[rgba(255,177,98,0.15)] text-[var(--accent)] text-sm"
          >
            {option.label}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                removeSelected(option.id);
              }}
              className="hover:text-[var(--accent)]/80"
            >
              <X className="h-3 w-3" strokeWidth={2.5} />
            </button>
          </span>
        ))}

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder={selected.length === 0 ? placeholder : ""}
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
        />
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 mt-2 w-full max-h-64 overflow-y-auto bg-[var(--surface-elevated)] border border-[var(--border-strong)] rounded-md shadow-lg"
             style={{ background: "var(--surface)", borderColor: "var(--border-strong)" }}>
          {filtered.length === 0 ? (
            <div className="p-3 text-sm text-[var(--text-muted)] text-center">
              No matches found
            </div>
          ) : (
            filtered.map((option) => {
              const isSelected = selected.includes(option.id);
              const isDisabled = !isSelected && atMax;

              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => toggle(option.id)}
                  disabled={isDisabled}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors",
                    isSelected && "bg-[rgba(255,177,98,0.1)] text-[var(--accent)]",
                    !isSelected && "text-[var(--text-primary)] hover:bg-[var(--surface-hover)]",
                    isDisabled && "opacity-40 cursor-not-allowed"
                  )}
                >
                  <div
                    className={cn(
                      "h-4 w-4 rounded border flex items-center justify-center shrink-0",
                      isSelected
                        ? "bg-[var(--accent)] border-[var(--accent)]"
                        : "border-[var(--border-strong)]"
                    )}
                  >
                    {isSelected && <Check className="h-3 w-3 text-[var(--accent-fg)]" strokeWidth={3} />}
                  </div>
                  {option.label}
                </button>
              );
            })
          )}

          {atMax && (
            <div className="p-2 text-xs text-[var(--text-muted)] border-t border-[var(--border)] text-center">
              Maximum {maxSelections} selections reached
            </div>
          )}
        </div>
      )}
    </div>
  );
}
