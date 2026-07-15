"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { onboardingApi } from "@/features/onboarding/api";
import { NarrativeText } from "@/components/shared/narrative-text";
import { CareerGraph } from "./career-graph";
import { ExtractionLog } from "./extraction-log";

interface StepBuildingProps {
  onComplete: () => void;
}

export function StepBuilding({ onComplete }: StepBuildingProps) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);

  // Start graph building on mount
  useEffect(() => {
    const startBuilding = async () => {
      try {
        const response = await onboardingApi.buildGraph();
        setJobId(response.job_id);
      } catch (error) {
        console.error("Failed to start graph building:", error);
      }
    };
    startBuilding();
  }, []);

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await onboardingApi.getGraphStatus(jobId);
        setStatus(response);

        if (response.status === "completed") {
          clearInterval(pollInterval);
          setGraphData(response.result);
          
          // Wait for animation to complete, then redirect
          setTimeout(() => {
            onComplete();
          }, 3000);
        } else if (response.status === "failed") {
          clearInterval(pollInterval);
          console.error("Graph building failed:", response.error);
        }
      } catch (error) {
        clearInterval(pollInterval);
        console.error("Failed to poll status:", error);
      }
    }, 800);

    return () => clearInterval(pollInterval);
  }, [jobId, onComplete]);

  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 space-y-8">
      {/* Header */}
      <div className="text-center">
        <NarrativeText size="2xl" weight="semibold" className="mb-2">
          Building your Career Graph.
        </NarrativeText>
        {status && (
          <NarrativeText size="sm" className="text-[var(--text-secondary)]">
            {status.progress}% complete
          </NarrativeText>
        )}
      </div>

      {/* Career Graph Visualization */}
      {graphData && (
        <div className="w-full max-w-2xl bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
          <CareerGraph data={graphData} />
        </div>
      )}

      {/* Progress Bar */}
      {status && (
        <div className="w-full max-w-md">
          <div className="h-1 bg-[var(--surface-hover)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--accent)] transition-all duration-700 ease-out"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Extraction Log */}
      {status && (
        <div className="w-full max-w-md">
          <ExtractionLog logs={status.logs} />
        </div>
      )}

      {/* Final Message */}
      {status?.status === "completed" && (
        <div className="text-center animate-fade-in space-y-1">
          <NarrativeText size="lg" className="text-[var(--success)]" weight="semibold">
            Your Career Graph is ready.
          </NarrativeText>
          <NarrativeText size="sm" className="text-[var(--text-muted)]">
            Redirecting to your first briefing...
          </NarrativeText>
        </div>
      )}
    </div>
  );
}
