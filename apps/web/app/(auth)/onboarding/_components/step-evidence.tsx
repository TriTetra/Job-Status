"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { FileText } from "lucide-react";
import { onboardingApi } from "@/features/onboarding/api";
import { NarrativeText } from "@/components/shared/narrative-text";
import { ExtractionResult } from "./extraction-result";

interface StepEvidenceProps {
  onComplete: () => void;
}

type Phase = "upload" | "processing" | "done";

export function StepEvidence({ onComplete }: StepEvidenceProps) {
  const [phase, setPhase] = useState<Phase>("upload");
  const [filename, setFilename] = useState("");
  const [progress, setProgress] = useState(0);
  const [logLine, setLogLine] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Önceki oturumda yüklenmişse → doğrudan review
  useEffect(() => {
    onboardingApi.getState().then((s) => {
      if (s.profile_data?.resume_doc_id) setPhase("done");
    }).catch(() => {});
  }, []);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setError("Too large — PDFs up to 25 MB");
      return;
    }
    setError(null);
    setFilename(file.name);
    setPhase("processing");
    setProgress(5);
    setLogLine("Uploading…");

    let jobId: string;
    try {
      const res = await onboardingApi.uploadResume(file);
      jobId = res.job_id;
    } catch {
      setError("Upload failed. Please try again.");
      setPhase("upload");
      return;
    }

    const poller = setInterval(async () => {
      try {
        const status = await onboardingApi.getResumeStatus(jobId);
        setProgress(status.progress ?? 50);
        if (status.logs?.length) {
          const msg = status.logs[status.logs.length - 1].message ?? "";
          setLogLine(msg.replace(/[\u{1F300}-\u{1FFFF}]/gu, "").trim());
        }
        if (status.status === "completed") {
          clearInterval(poller);
          setProgress(100);
          setPhase("done");
        } else if (status.status === "failed") {
          clearInterval(poller);
          setError(status.error ?? "Extraction failed");
          setPhase("upload");
        }
      } catch {
        clearInterval(poller);
        setError("Connection lost. Please try again.");
        setPhase("upload");
      }
    }, 1000);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  // ── Upload ──
  if (phase === "upload") {
    return (
      <div className="space-y-3">
        <div>
          <NarrativeText size="xl" weight="semibold">Show us your work.</NarrativeText>
          <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            Upload your CV and we&apos;ll map your skills automatically.
          </p>
        </div>

        {error && (
          <div className="px-3 py-2 rounded-lg border text-xs" style={{ background: "rgba(235,94,85,0.08)", borderColor: "rgba(235,94,85,0.2)", color: "var(--danger)" }}>
            {error}
          </div>
        )}

        <div>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">Resume / CV *</label>
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed cursor-pointer py-8 transition-all"
            style={{ borderColor: isDragging ? "var(--accent)" : "var(--border)", background: isDragging ? "rgba(255,177,98,0.04)" : "var(--surface)" }}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
            <FileText className="h-7 w-7" strokeWidth={1.5} style={{ color: "var(--text-muted)" }} />
            <div className="text-center">
              <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{isDragging ? "Drop here" : "Drag & drop or click to browse"}</p>
              <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>PDF only · up to 25 MB</p>
            </div>
          </div>
        </div>

        <button type="button" onClick={onComplete} className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all" style={{ background: "var(--surface-hover)", color: "var(--text-muted)", cursor: "pointer" }}>
          Skip for now
        </button>
      </div>
    );
  }

  // ── Processing ──
  if (phase === "processing") {
    return (
      <div className="space-y-3">
        <div>
          <NarrativeText size="xl" weight="semibold">Analyzing your CV</NarrativeText>
          <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>Extracting skills, experience, and projects…</p>
        </div>
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
          <FileText className="h-4 w-4 shrink-0" strokeWidth={1.5} style={{ color: "var(--accent)" }} />
          <span className="text-sm flex-1 truncate" style={{ color: "var(--text-primary)" }}>{filename}</span>
          <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>{progress}%</span>
        </div>
        <div className="h-0.5 rounded-full overflow-hidden" style={{ background: "var(--surface-hover)" }}>
          <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${progress}%`, background: "var(--accent)" }} />
        </div>
        {logLine && <p className="text-[12px] truncate" style={{ color: "var(--text-muted)" }}>{logLine}</p>}
      </div>
    );
  }

  // ── Done → Evidence Review ──
  return <ExtractionResult onComplete={onComplete} />;
}
