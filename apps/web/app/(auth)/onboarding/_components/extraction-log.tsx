"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, Info } from "lucide-react";

interface LogEntry {
  timestamp: string;
  message: string;
  type: "info" | "success" | "error";
}

interface ExtractionLogProps {
  logs: LogEntry[];
}

export function ExtractionLog({ logs }: ExtractionLogProps) {
  const [visibleLogs, setVisibleLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    // Typewriter effect: add logs one by one
    if (logs.length > visibleLogs.length) {
      const timer = setTimeout(() => {
        setVisibleLogs(logs.slice(0, visibleLogs.length + 1));
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [logs, visibleLogs]);

  const getIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-[var(--success)]" strokeWidth={2} />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-[var(--danger)]" strokeWidth={2} />;
      default:
        return <Info className="h-4 w-4 text-[var(--accent)]" strokeWidth={2} />;
    }
  };

  return (
    <div className="bg-[var(--surface-elevated)] rounded-lg p-4 font-mono text-sm space-y-2 max-h-64 overflow-y-auto custom-scrollbar"
         style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
      {visibleLogs.map((log, index) => (
        <div
          key={index}
          className="flex items-start gap-2 animate-fade-in"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <div className="mt-0.5">{getIcon(log.type)}</div>
          <span className="text-[var(--text-secondary)] leading-relaxed">
            {log.message}
          </span>
        </div>
      ))}
      {visibleLogs.length < logs.length && (
        <div className="flex items-center gap-2 text-[var(--text-muted)]">
          <div className="h-4 w-4 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
          <span>Processing...</span>
        </div>
      )}
    </div>
  );
}
