"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface Option {
  id: string;
  label: string;
}

interface ChipMultiSelectProps {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
  maxSelections?: number;
  minSelections?: number;
}

export function ChipMultiSelect({
  options,
  selected,
  onChange,
  maxSelections = 3,
  minSelections = 0,
}: ChipMultiSelectProps) {
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

  const atMax = selected.length >= maxSelections;

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const isSelected = selected.includes(option.id);
        const isDisabled = !isSelected && atMax;

        return (
          <button
            key={option.id}
            type="button"
            onClick={() => toggle(option.id)}
            disabled={isDisabled}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-150",
              "border",
              isSelected
                ? "bg-[rgba(255,177,98,0.15)] text-[var(--accent)] border-[rgba(255,177,98,0.3)]"
                : "bg-[var(--surface)] text-[var(--text-secondary)] border-[var(--border)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)]",
              isDisabled && "opacity-40 cursor-not-allowed"
            )}
          >
            {isSelected && <Check className="h-3.5 w-3.5" strokeWidth={2.5} />}
            {option.label}
          </button>
        );
      })}

      {atMax && (
        <div className="w-full mt-2 text-xs text-[var(--text-muted)]">
          Maximum {maxSelections} selections reached.
        </div>
      )}
    </div>
  );
}
