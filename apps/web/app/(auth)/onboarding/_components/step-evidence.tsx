"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { FileText, Github, Globe, Check } from "lucide-react";
import { onboardingApi } from "@/features/onboarding/api";
import { NarrativeText } from "@/components/shared/narrative-text";

interface StepEvidenceProps {
  onComplete: () => void;
}

type Phase = "upload" | "processing" | "done";

export function StepEvidence({ onComplete }: StepEvidenceProps) {
  const [phase, setPhase]           = useState<Phase>("upload");
  const [filename, setFilename]     = useState("");
  const [progress, setProgress]     = useState(0);
  const [logLine, setLogLine]       = useState("");
  const [skills, setSkills]         = useState<string[]>([]);
  const [showAll, setShowAll]       = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  // Portfolio
  const [portfolioOpen, setPortfolioOpen]       = useState(false);
  const [portfolioUrl, setPortfolioUrl]         = useState("");
  const [portfolioConnected, setPortfolioConnected] = useState(false);
  const [crawling, setCrawling]                 = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Already uploaded in a prior session → skip to done
  useEffect(() => {
    onboardingApi.getState().then((s) => {
      if (s.profile_data?.resume_doc_id) fetchSkillsAndDone();
    }).catch(() => {});
  }, []);

  const fetchSkillsAndDone = useCallback(() => {
    onboardingApi.getAggregatedSkills()
      .then((d) => {
        setSkills(d.skills.map((s: any) => s.skill_name));
        setPhase("done");
      })
      .catch(() => setPhase("done"));
  }, []);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted");
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
          fetchSkillsAndDone();
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
  }, [fetchSkillsAndDone]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleCrawl = async () => {
    if (!portfolioUrl) return;
    setCrawling(true);
    try {
      await onboardingApi.crawlPortfolio(portfolioUrl);
      setPortfolioConnected(true);
      setPortfolioOpen(false);
      fetchSkillsAndDone(); // refresh skills
    } catch {
      // silently fail — user can try again
    } finally {
      setCrawling(false);
    }
  };

  // ── Shared label style ────────────────────────────────────────────────────
  const labelCls = "block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]";

  // ── Shared chip toggle style ───────────────────────────────────────────────
  const chipActive = {
    borderColor: "var(--accent)",
    background: "rgba(255,177,98,0.05)",
    color: "var(--accent)",
  } as const;
  const chipIdle = {
    borderColor: "var(--border)",
    background: "var(--surface)",
    color: "var(--text-secondary)",
  } as const;

  // ─── Upload ───────────────────────────────────────────────────────────────
  if (phase === "upload") {
    return (
      <div className="space-y-3">
        <div>
          <NarrativeText size="xl" weight="semibold">Show us your work.</NarrativeText>
          <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            Upload your CV and we'll map your skills automatically.
          </p>
        </div>

        {error && (
          <div
            className="px-3 py-2 rounded-lg border text-xs"
            style={{ background: "rgba(235,94,85,0.08)", borderColor: "rgba(235,94,85,0.2)", color: "var(--danger)" }}
          >
            {error}
          </div>
        )}

        {/* Upload zone — same vertical rhythm as a field group */}
        <div>
          <label className={labelCls}>Resume / CV *</label>
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed cursor-pointer py-8 transition-all"
            style={{
              borderColor: isDragging ? "var(--accent)" : "var(--border)",
              background:  isDragging ? "rgba(255,177,98,0.04)" : "var(--surface)",
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <FileText className="h-7 w-7" strokeWidth={1.5} style={{ color: "var(--text-muted)" }} />
            <div className="text-center">
              <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                {isDragging ? "Drop here" : "Drag & drop or click to browse"}
              </p>
              <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>PDF only · up to 10 MB</p>
            </div>
          </div>
        </div>

        {/* Skip */}
        <button
          type="button"
          onClick={onComplete}
          className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
          style={{ background: "var(--surface-hover)", color: "var(--text-muted)", cursor: "pointer" }}
        >
          Skip for now
        </button>
      </div>
    );
  }

  // ─── Processing ───────────────────────────────────────────────────────────
  if (phase === "processing") {
    return (
      <div className="space-y-3">
        <div>
          <NarrativeText size="xl" weight="semibold">Analyzing your CV</NarrativeText>
          <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            Extracting skills, experience, and projects…
          </p>
        </div>

        {/* File row — same height as an input */}
        <div
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}
        >
          <FileText className="h-4 w-4 shrink-0" strokeWidth={1.5} style={{ color: "var(--accent)" }} />
          <span className="text-sm flex-1 truncate" style={{ color: "var(--text-primary)" }}>{filename}</span>
          <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>{progress}%</span>
        </div>

        {/* Thin progress bar — matches wizard step bar style */}
        <div className="h-0.5 rounded-full overflow-hidden" style={{ background: "var(--surface-hover)" }}>
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progress}%`, background: "var(--accent)" }}
          />
        </div>

        {logLine && (
          <p className="text-[12px] truncate" style={{ color: "var(--text-muted)" }}>{logLine}</p>
        )}
      </div>
    );
  }

  // ─── Done ─────────────────────────────────────────────────────────────────
  const VISIBLE = 10;
  const displayedSkills = showAll ? skills : skills.slice(0, VISIBLE);
  const overflow = skills.length - VISIBLE;

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="space-y-3">
      <div>
        <NarrativeText size="xl" weight="semibold">
          {skills.length > 0 ? `Found ${skills.length} skills` : "CV analyzed"}
        </NarrativeText>
        <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
          Connect more sources to strengthen your signals.
        </p>
      </div>

      {/* Sources */}
      <div>
        <label className={labelCls}>Sources</label>
        <div className="flex flex-wrap gap-1.5">
          {/* CV — always connected */}
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium"
            style={chipActive}
          >
            <Check className="h-3 w-3" strokeWidth={2.5} />
            CV uploaded
          </span>

          {/* GitHub */}
          <button
            type="button"
            onClick={() => { window.location.href = `${apiBase}/api/oauth/github/authorize`; }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all"
            style={chipIdle}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--border)"; }}
          >
            <Github className="h-3 w-3" />
            Add GitHub
          </button>

          {/* Portfolio */}
          {portfolioConnected ? (
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium"
              style={chipActive}
            >
              <Check className="h-3 w-3" strokeWidth={2.5} />
              Portfolio
            </span>
          ) : (
            <button
              type="button"
              onClick={() => setPortfolioOpen((v) => !v)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all"
              style={portfolioOpen ? chipActive : chipIdle}
              onMouseEnter={(e) => { if (!portfolioOpen) (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)"; }}
              onMouseLeave={(e) => { if (!portfolioOpen) (e.currentTarget as HTMLElement).style.borderColor = "var(--border)"; }}
            >
              <Globe className="h-3 w-3" />
              Add Portfolio
            </button>
          )}
        </div>

        {/* Portfolio URL — inline expand */}
        {portfolioOpen && !portfolioConnected && (
          <div className="flex gap-2 mt-2">
            <input
              type="url"
              value={portfolioUrl}
              onChange={(e) => setPortfolioUrl(e.target.value)}
              placeholder="https://your-portfolio.com"
              className="flex-1 px-3 py-1.5 rounded-lg border text-sm outline-none transition-colors"
              style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
              onKeyDown={(e) => e.key === "Enter" && handleCrawl()}
            />
            <button
              type="button"
              onClick={handleCrawl}
              disabled={!portfolioUrl || crawling}
              className="px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all disabled:opacity-40"
              style={chipActive}
            >
              {crawling ? "…" : "Add"}
            </button>
          </div>
        )}
      </div>

      {/* Skills */}
      {skills.length > 0 && (
        <div>
          <label className={labelCls}>Skills detected</label>
          <div className="flex flex-wrap gap-1.5">
            {displayedSkills.map((name) => (
              <span
                key={name}
                className="inline-flex items-center px-3 py-1.5 rounded-full border text-xs font-medium"
                style={chipIdle}
              >
                {name}
              </span>
            ))}
            {!showAll && overflow > 0 && (
              <button
                type="button"
                onClick={() => setShowAll(true)}
                className="inline-flex items-center px-3 py-1.5 rounded-full border text-xs font-medium transition-all"
                style={{ borderColor: "var(--border)", background: "transparent", color: "var(--text-muted)" }}
              >
                +{overflow} more
              </button>
            )}
          </div>
        </div>
      )}

      {/* Continue */}
      <button
        type="button"
        onClick={onComplete}
        className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all"
        style={{ background: "var(--accent)", color: "var(--accent-fg)", cursor: "pointer" }}
      >
        Continue
      </button>
    </div>
  );
}
