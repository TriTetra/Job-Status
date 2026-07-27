"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Search, ChevronDown, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ComboboxOption {
  id: string;
  title: string;
  category: string;
  aliases?: string[];
  slug?: string;
}

interface SearchableComboboxProps {
  /** Pre-loaded options (static fallback / initial hydration) */
  initialOptions?: ComboboxOption[];
  /** Async search function (backend API) */
  onSearch?: (query: string) => Promise<ComboboxOption[]>;
  /** Currently selected value (id) */
  value: string;
  /** Callback when selection changes */
  valueLabel?: string;          // ← YENİ EKLE
  onChange: (id: string, title: string) => void;
  placeholder?: string;
  emptyMessage?: string;
  /** Allow user to create custom entries not in the list */
  allowCustom?: boolean;
  /** Label template for the custom option — use {query} as placeholder */
  customLabel?: string;
  className?: string;
}

/**
 * SearchableCombobox
 *
 * Hybrid search: uses static initialOptions for instant first render,
 * then fetches from backend API via onSearch for live results.
 *
 * - Debounced search (300ms)
 * - Category grouping
 * - Keyboard navigation (↑↓ Enter Esc)
 * - "Use custom" escape hatch
 * - WAI-ARIA accessible
 * - Loading state
 */
export function SearchableCombobox({
  initialOptions = [],
  onSearch,
  value,
  valueLabel,
  onChange,
  placeholder = "Search...",
  emptyMessage = "No matches found",
  allowCustom = true,
  customLabel = 'Use "{query}" as custom',
  className,
}: SearchableComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ComboboxOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const selectedOption =
    initialOptions.find((o) => o.id === value) ||
    results.find((o) => o.id === value);

  // Option listede bulunamasa bile label'ı göster.
  const displayLabel = value
    ? (selectedOption?.title ?? valueLabel ?? "")
    : "";

  // ─── Search ──────────────────────────────────────────────────

  const performSearch = useCallback(
    async (searchQuery: string) => {
      const q = searchQuery.trim();

      if (!q) {
        setResults(initialOptions.slice(0, 15));
        setIsLoading(false);
        return;
      }

      if (onSearch) {
        setIsLoading(true);
        try {
          const apiResults = await onSearch(q);
          setResults(apiResults);
        } catch {
          setResults(clientSideSearch(initialOptions, q));
        } finally {
          setIsLoading(false);
        }
      } else {
        setResults(clientSideSearch(initialOptions, q));
        setIsLoading(false);
      }

      setHighlightedIndex(0);
    },
    [initialOptions, onSearch]
  );

  useEffect(() => {
    if (!isOpen) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => performSearch(query), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, isOpen, performSearch]);

  useEffect(() => {
    if (isOpen && results.length === 0 && !query) {
      setResults(initialOptions.slice(0, 15));
    }
  }, [isOpen, initialOptions, query, results.length]);

  // ─── Grouping ─────────────────────────────────────────────────

  const grouped = results.reduce(
    (acc, option) => {
      const cat = option.category || "Other";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(option);
      return acc;
    },
    {} as Record<string, ComboboxOption[]>
  );

  const flatResults = Object.values(grouped).flat();
  const showCustomOption =
    allowCustom &&
    query.trim().length > 0 &&
    !flatResults.some(
      (o) => o.title.toLowerCase() === query.trim().toLowerCase()
    );

  // ─── Handlers ─────────────────────────────────────────────────

  const handleSelect = (id: string, title: string) => {
    onChange(id, title);
    setIsOpen(false);
    setQuery("");
    setResults([]);
  };

  const handleCustomSelect = () => {
    const customTitle = query.trim();
    const customId = `custom_${customTitle.toLowerCase().replace(/\s+/g, "_")}`;
    handleSelect(customId, customTitle);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const totalItems = flatResults.length + (showCustomOption ? 1 : 0);

    if (!isOpen) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setIsOpen(true);
        inputRef.current?.focus();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightedIndex((prev) => Math.min(prev + 1, totalItems - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (highlightedIndex < flatResults.length) {
          const sel = flatResults[highlightedIndex];
          handleSelect(sel.id, sel.title);
        } else if (showCustomOption) {
          handleCustomSelect();
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setQuery("");
        break;
    }
  };

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

  // ─── Render ───────────────────────────────────────────────────

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger */}
      <div
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border text-sm cursor-text transition-colors"
        style={{
          background: "var(--surface)",
          borderColor: isOpen ? "var(--accent)" : "var(--border)",
        }}
        onClick={() => {
          setIsOpen(true);
          inputRef.current?.focus();
        }}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <Search className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} strokeWidth={1.75} />
        <input
          ref={inputRef}
          type="text"
          value={isOpen ? query : displayLabel}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="flex-1 bg-transparent outline-none min-w-0"
          style={{ color: "var(--text-primary)" }}
          aria-autocomplete="list"
          aria-controls="combobox-listbox"
        />
        {isLoading && (
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" style={{ color: "var(--text-muted)" }} />
        )}
        {value && !isOpen && (
          <button
            onClick={(e) => { e.stopPropagation(); handleSelect("", ""); }}
            className="shrink-0 hover:opacity-80 transition-opacity"
            style={{ color: "var(--text-muted)" }}
            aria-label="Clear selection"
          >
            <X className="h-3.5 w-3.5" strokeWidth={2} />
          </button>
        )}
        <ChevronDown
          className="h-4 w-4 shrink-0 transition-transform"
          style={{ color: "var(--text-muted)", transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}
          strokeWidth={1.75}
        />
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          id="combobox-listbox"
          role="listbox"
          className="absolute z-50 w-full mt-1.5 rounded-lg border shadow-lg max-h-72 overflow-y-auto"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          {isLoading && flatResults.length === 0 ? (
            <div className="flex items-center justify-center gap-2 p-4 text-sm" style={{ color: "var(--text-muted)" }}>
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching...
            </div>
          ) : flatResults.length === 0 && !showCustomOption ? (
            <div className="p-4 text-sm text-center" style={{ color: "var(--text-muted)" }}>
              {emptyMessage}
            </div>
          ) : (
            <>
              {Object.entries(grouped).map(([category, items]) => (
                <div key={category} role="group" aria-label={category}>
                  <div
                    className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider sticky top-0 z-10"
                    style={{
                      color: "var(--text-muted)",
                      background: "var(--surface-hover)",
                      borderBottom: "1px solid var(--border)",
                    }}
                  >
                    {category}
                  </div>
                  {items.map((option) => {
                    const globalIndex = flatResults.findIndex((o) => o.id === option.id);
                    const isHighlighted = globalIndex === highlightedIndex;
                    const isSelected = option.id === value;

                    return (
                      <button
                        key={option.id}
                        role="option"
                        aria-selected={isSelected}
                        onClick={() => handleSelect(option.id, option.title)}
                        onMouseEnter={() => setHighlightedIndex(globalIndex)}
                        className="w-full px-3 py-2 text-sm text-left transition-colors flex items-center justify-between gap-2"
                        style={{
                          background: isHighlighted ? "var(--surface-hover)" : "transparent",
                          color: isSelected ? "var(--accent)" : "var(--text-primary)",
                        }}
                      >
                        <span className="truncate">{option.title}</span>
                        {isSelected && (
                          <span className="shrink-0 text-xs font-medium" style={{ color: "var(--accent)" }}>✓</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}

              {showCustomOption && (
                <button
                  role="option"
                  aria-selected={false}
                  onClick={handleCustomSelect}
                  onMouseEnter={() => setHighlightedIndex(flatResults.length)}
                  className="w-full px-3 py-2.5 text-sm text-left transition-colors border-t"
                  style={{
                    borderColor: "var(--border)",
                    background: highlightedIndex === flatResults.length ? "var(--surface-hover)" : "transparent",
                    color: "var(--text-secondary)",
                  }}
                >
                  <span style={{ color: "var(--accent)" }}>+</span>{" "}
                  {customLabel.replace("{query}", query.trim())}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Client-side fallback search ──────────────────────────────

function clientSideSearch(options: ComboboxOption[], query: string): ComboboxOption[] {
  const q = query.toLowerCase().trim();
  if (!q) return options.slice(0, 15);

  return options
    .map((option) => {
      let score = 0;
      const titleLower = option.title.toLowerCase();
      const aliasesLower = (option.aliases ?? []).map((a) => a.toLowerCase());

      if (titleLower === q) score += 1000;
      else if (titleLower.startsWith(q)) score += 500;
      else if (titleLower.includes(q)) score += 200;

      if (aliasesLower.some((a) => a === q)) score += 300;
      else if (aliasesLower.some((a) => a.includes(q))) score += 100;

      if (option.category.toLowerCase().includes(q)) score += 50;

      return { option, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10)
    .map((x) => x.option);
}
