"use client";

import type { Opportunity, Criterion } from "@/features/opportunities/types";
import { Button } from "@/components/shared/button";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Check, X, Minus, Loader2 } from "lucide-react";
import { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { WhyModal } from "./why-modal";

interface OpportunityDetailPanelProps {
  opp: Opportunity;
  onApply: () => void;
  onShortlist: () => void;
  onSkip: () => void;
}

function CriterionIcon({ state }: { state: Criterion["state"] }) {
  if (state === "confirmed") {
    return <Check className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--success)" }} />;
  }
  if (state === "conflict") {
    return <X className="h-4 w-4" strokeWidth={2.5} style={{ color: "var(--danger)" }} />;
  }
  return <Minus className="h-4 w-4" strokeWidth={2} style={{ color: "var(--text-muted)" }} />;
}

/**
 * Sağ panel — decision surface.
 * Newsreader italic reasoning, criteria checklist, evidence, actions.
 */
export function OpportunityDetailPanel({
  opp,
  onApply,
  onShortlist,
  onSkip,
}: OpportunityDetailPanelProps) {
  const [decision, setDecision] = useState(opp.decision);
  const { explanation } = opp;
  const [whyOpen, setWhyOpen] = useState(false);
  const [reasoningLoading, setReasoningLoading] = useState(false);

  const company = explanation?.company ?? "Unknown";
  const title = explanation?.title ?? "Open role";
  const location = explanation?.location ?? "—";
  const remote = explanation?.remote ?? false;
  const region = explanation?.remote_region;
  const source = explanation?.source;
  const scannedAt = opp.scanned_at;

  const criteria = decision?.criteria ?? [];
  const reasoning = decision?.reasoning;
  const nextAction = decision?.next_action;

  const matchedSkills: Array<{ name: string; confidence: number }> =
    explanation?.matched_skills ?? [];
  const gapSkills: string[] = opp.skill_gaps ?? [];

  // On-demand reasoning: generated (and cached server-side) on first open
  const fetchReasoning = async () => {
    if (reasoning) {
      setWhyOpen(true);
      return;
    }
    setReasoningLoading(true);
    try {
      const res = await apiFetch<{ decision: NonNullable<Opportunity["decision"]> }>(
        `/api/jobs/reasoning/${encodeURIComponent(opp.url)}`
      );
      setDecision(res.decision);
      setWhyOpen(true);
    } catch (err) {
      console.error("[opportunity] reasoning failed:", err);
    } finally {
      setReasoningLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col p-8 overflow-y-auto custom-scrollbar">
      {/* Header */}
      <div className="mb-6">
        <NarrativeText size="2xl" weight="semibold" className="mb-1">
          {title}
        </NarrativeText>
        <div className="text-base" style={{ color: "var(--text-secondary)" }}>
          {company}
        </div>
        <div className="text-sm mt-2 flex items-center gap-3 flex-wrap" style={{ color: "var(--text-muted)" }}>
          {remote && region ? (
            <span>Remote · {region}</span>
          ) : remote ? (
            <span>Remote</span>
          ) : (
            <span>{location}</span>
          )}
          {source && source !== "unknown" && (
            <>
              <span>·</span>
              <span>via {source}</span>
            </>
          )}
          {scannedAt && (
            <>
              <span>·</span>
              <span>
                {new Date(scannedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Reasoning (Newsreader italic) */}
      {reasoning && (
        <div className="mb-8 pb-6 border-b" style={{ borderColor: "var(--border)" }}>
          <div
            className="text-[11px] font-semibold tracking-wider uppercase mb-3"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
          >
            Why this is worth it
          </div>
          <p
            className="text-base leading-relaxed"
            style={{ fontFamily: "var(--font-editorial)", fontStyle: "italic", color: "var(--text-primary)" }}
          >
            {reasoning}
          </p>
        </div>
      )}

      {/* Criteria checklist */}
      {criteria.length > 0 && (
        <div className="mb-8 pb-6 border-b" style={{ borderColor: "var(--border)" }}>
          <div
            className="text-[11px] font-semibold tracking-wider uppercase mb-3"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
          >
            Fit against your priorities
          </div>
          <div className="space-y-2">
            {criteria.map((c) => (
              <div key={c.key} className="flex items-start gap-2">
                <div className="mt-0.5 shrink-0">
                  <CriterionIcon state={c.state} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {c.label}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {c.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence + Gaps */}
      {(matchedSkills.length > 0 || gapSkills.length > 0) && (
        <div className="mb-8 pb-6 border-b" style={{ borderColor: "var(--border)" }}>
          {matchedSkills.length > 0 && (
            <>
              <div
                className="text-[11px] font-semibold tracking-wider uppercase mb-2"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
              >
                Strong matches
              </div>
              <div className="flex flex-wrap gap-1.5 mb-4">
                {matchedSkills.map((s) => (
                  <span
                    key={s.name}
                    className="px-2.5 py-1 rounded-full border text-xs font-medium"
                    style={{
                      borderColor: "var(--success)",
                      background: "rgba(127, 182, 133, 0.08)",
                      color: "var(--success)",
                    }}
                  >
                    {s.name}
                  </span>
                ))}
              </div>
            </>
          )}
          {gapSkills.length > 0 && (
            <>
              <div
                className="text-[11px] font-semibold tracking-wider uppercase mb-2"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
              >
                Gaps
              </div>
              <div className="flex flex-wrap gap-1.5">
                {gapSkills.map((g) => (
                  <span
                    key={g}
                    className="px-2.5 py-1 rounded-full border text-xs font-medium"
                    style={{
                      borderColor: "var(--danger)",
                      background: "rgba(201, 106, 90, 0.08)",
                      color: "var(--danger)",
                    }}
                  >
                    {g}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-auto pt-6 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="mb-4">
          <div
            className="text-[11px] font-semibold tracking-wider uppercase mb-2"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}
          >
            Recommended next step
          </div>
          {nextAction && (
            <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                {nextAction.label}
              </span>
              {nextAction.reason && <span> — {nextAction.reason}</span>}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mb-3">
          <Button variant="primary" onClick={onApply}>
            Apply
          </Button>
          <Button variant="outline" onClick={onShortlist}>
            Shortlist
          </Button>
          <Button variant="ghost" onClick={onSkip}>
            Skip
          </Button>
        </div>

        <button
          onClick={fetchReasoning}
          disabled={reasoningLoading}
          className="text-xs font-medium flex items-center gap-1 transition-colors bg-transparent border-0 p-0 cursor-pointer"
          style={{ color: "var(--accent)" }}
        >
          {reasoningLoading ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Generating explanation…
            </>
          ) : (
            <>
              Why {opp.career_score ?? 0}?
            </>
          )}
        </button>
      </div>

      {whyOpen && <WhyModal opp={{ ...opp, decision }} onClose={() => setWhyOpen(false)} />}
    </div>
  );
}
