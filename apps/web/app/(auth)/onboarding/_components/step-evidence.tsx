"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { onboardingApi } from "@/features/onboarding/api";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { ExtractionLog } from "./extraction-log";

interface StepEvidenceProps {
  onComplete: () => void;
}

export function StepEvidence({ onComplete }: StepEvidenceProps) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await onboardingApi.getResumeStatus(jobId);
        setStatus(response);

        if (response.status === "completed") {
          clearInterval(pollInterval);
          setTimeout(() => onComplete(), 1500);
        } else if (response.status === "failed") {
          clearInterval(pollInterval);
          setError(response.error || "Extraction failed");
        }
      } catch (err) {
        clearInterval(pollInterval);
        setError("Failed to check status");
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [jobId, onComplete]);

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError("Only PDF files are accepted");
      return;
    }

    setError(null);
    setFile(selectedFile);

    try {
      const response = await onboardingApi.uploadResume(selectedFile);
      setJobId(response.job_id);
    } catch (err) {
      setError("Failed to upload resume");
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFileSelect(droppedFile);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  return (
    <div className="space-y-12">
      {/* Narrative Opening */}
      <div>
        <NarrativeText size="2xl" weight="semibold" className="mb-2">
          Show us your work.
        </NarrativeText>
        <NarrativeText size="base" className="text-[var(--text-secondary)]">
          Upload your resume and we'll extract evidence of your skills.
        </NarrativeText>
      </div>

      {/* Upload Zone */}
      {!jobId && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
            transition-all duration-200
            ${isDragging 
              ? "border-[var(--accent)] bg-[rgba(255,177,98,0.05)]" 
              : "border-[var(--border)] hover:border-[var(--accent)]/50 hover:bg-[var(--surface-hover)]"
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            className="hidden"
          />

          <Upload className="h-12 w-12 mx-auto mb-4 text-[var(--text-muted)]" strokeWidth={1.5} />
          <NarrativeText size="lg" weight="medium" className="mb-2">
            {isDragging ? "Drop your resume here" : "Drag & drop your resume"}
          </NarrativeText>
          <NarrativeText size="sm" className="text-[var(--text-muted)]">
            or click to browse (PDF only)
          </NarrativeText>
        </div>
      )}

      {/* Extraction Progress */}
      {jobId && status && (
        <div className="space-y-6">
          {/* File Info */}
          <div className="flex items-center gap-3 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-lg">
            <FileText className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.5} />
            <div className="flex-1 min-w-0">
              <NarrativeText size="sm" weight="medium" className="truncate">
                {file?.name}
              </NarrativeText>
              <NarrativeText size="sm" className="text-[var(--text-muted)]">
                {status.status === "completed" ? "Extraction complete" : `Processing... ${status.progress}%`}
              </NarrativeText>
            </div>
            {status.status === "completed" && (
              <CheckCircle2 className="h-5 w-5 text-[var(--success)]" strokeWidth={2} />
            )}
            {status.status === "failed" && (
              <AlertCircle className="h-5 w-5 text-[var(--danger)]" strokeWidth={2} />
            )}
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="h-1 bg-[var(--surface-hover)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--accent)] transition-all duration-500 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          {/* Extraction Log */}
          <ExtractionLog logs={status.logs} />

          {/* Result Summary */}
          {status.status === "completed" && status.result && (
            <div className="p-4 bg-[rgba(127,182,133,0.1)] border border-[rgba(127,182,133,0.2)] rounded-lg space-y-2">
              <NarrativeText size="sm" weight="semibold" className="text-[var(--success)]">
                Career Graph ready
              </NarrativeText>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-[var(--text-muted)]">Skills:</span>{" "}
                  <span className="font-mono font-medium">{status.result.skills_extracted}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Companies:</span>{" "}
                  <span className="font-mono font-medium">{status.result.companies_found}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Evidence:</span>{" "}
                  <span className="font-mono font-medium">{status.result.evidence_items}</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Confidence:</span>{" "}
                  <span className="font-mono font-medium">{Math.round(status.result.confidence_score * 100)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-[rgba(235,94,85,0.1)] border border-[rgba(235,94,85,0.2)] rounded-lg">
          <NarrativeText size="sm" className="text-[var(--danger)]">
            {error}
          </NarrativeText>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => {
              setError(null);
              setFile(null);
              setJobId(null);
              setStatus(null);
            }}
          >
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}
