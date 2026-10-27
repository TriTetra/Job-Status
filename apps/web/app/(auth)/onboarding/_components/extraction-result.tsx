"use client";

import { useState, useEffect } from "react";
import type { EvidenceReviewItem } from "@/features/onboarding/types";
import { NarrativeText } from "@/components/shared/narrative-text";
import { onboardingApi } from "@/features/onboarding/api";
import { Check, Github, FileText, Globe } from "lucide-react";

type AggregatedSkill = Awaited<ReturnType<typeof onboardingApi.getAggregatedSkills>>["skills"][number];

interface ExtractionResultProps {
  onComplete: () => void;
}

export function ExtractionResult({ onComplete }: ExtractionResultProps) {
  const [skills, setSkills] = useState<AggregatedSkill[]>([]);
  const [projects, setProjects] = useState<EvidenceReviewItem[]>([]);
  const [experiences, setExperiences] = useState<EvidenceReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([onboardingApi.getAggregatedSkills(), onboardingApi.getEvidenceItems()])
      .then(([agg, ev]) => {
        setSkills(agg.skills);
        setProjects(ev.projects);
        setExperiences(ev.experiences);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const conf = (c: number) => (c >= 0.85 ? "var(--success)" : c >= 0.7 ? "var(--warning,#e6a817)" : "var(--danger)");
  const srcDot = (t: string) =>
    t === "github" ? <Github className="h-2.5 w-2.5" /> : t === "portfolio" ? <Globe className="h-2.5 w-2.5" /> : <FileText className="h-2.5 w-2.5" />;

  if (loading) {
    return <div className="flex items-center justify-center py-12"><div className="animate-spin h-6 w-6 border-2 border-[var(--accent)] border-t-transparent rounded-full" /></div>;
  }

  const TOP_SKILLS = 8;
  const topSkills = skills.slice(0, TOP_SKILLS);
  const skillOverflow = skills.length - TOP_SKILLS;
  const topProjects = projects.slice(0, 2);
  const topExp = experiences.slice(0, 2);

  return (
    <div className="space-y-4">
      <div>
        <NarrativeText size="xl" weight="semibold">
          {skills.length > 0 ? `Found ${skills.length} skills` : "CV analyzed"}
        </NarrativeText>
        <p className="text-[13px] mt-0.5" style={{ color: "var(--text-muted)" }}>
          Review your evidence. Strengthen it on the next step.
        </p>
      </div>

      {/* Skills — 2 sütun compact grid */}
      {topSkills.length > 0 && (
        <section>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">Strongest signals</label>
          <div className="grid grid-cols-2 gap-1.5">
            {topSkills.map((s) => (
              <div key={s.skill_name} className="flex items-center gap-2 px-2.5 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-medium text-[var(--text-primary)] truncate">{s.skill_name}</span>
                    {s.canonical_id ? (
                      <span title="Verified against our skill catalog" className="shrink-0">
                        <Check className="h-3 w-3 text-[var(--success)]" />
                      </span>
                    ) : (
                      <span
                        title="Read from your CV — not yet in our catalog. Confirm it in Evidence Studio."
                        className="group relative inline-flex items-center gap-1 shrink-0 animate-fade-in"
                      >
                        <span className="relative flex h-3 w-3 items-center justify-center">
                          <span
                            className="absolute inset-0 rounded-full border border-dashed animate-[spin_6s_linear_infinite]"
                            style={{ borderColor: "var(--warning, #e6a817)" }}
                          />
                          <span className="h-1 w-1 rounded-full" style={{ background: "var(--warning, #e6a817)" }} />
                        </span>
                        <span
                          className="hidden group-hover:inline text-[9px] font-medium px-1.5 py-0.5 rounded -mr-1 transition-colors"
                          style={{ color: "var(--warning, #e6a817)", background: "rgba(230,168,23,0.1)" }}
                        >
                          extracted
                        </span>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 mt-0.5 text-[var(--text-muted)]">
                    {s.sources.map((src) => <span key={src.type}>{srcDot(src.type)}</span>)}
                  </div>
                </div>
                <span className="text-xs font-mono font-semibold shrink-0" style={{ color: conf(s.aggregated_confidence) }}>
                  {Math.round(s.aggregated_confidence * 100)}%
                </span>
              </div>
            ))}
            {skillOverflow > 0 && (
              <div className="flex items-center justify-center px-2.5 py-2 rounded-lg border border-dashed border-[var(--border)] text-xs text-[var(--text-muted)]">
                +{skillOverflow} more
              </div>
            )}
          </div>
        </section>
      )}

      {/* Projects — 2 sütun */}
      {topProjects.length > 0 && (
        <section>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">Projects</label>
          <div className="grid grid-cols-2 gap-1.5">
            {topProjects.map((p) => (
              <div key={p.id} className="px-2.5 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-medium text-[var(--text-primary)] truncate">{p.name}</span>
                  <Check className="h-3 w-3 text-[var(--success)] shrink-0 ml-auto" />
                </div>
                {(p.evidence_data.technologies?.length ?? 0) > 0 && (
                  <p className="text-[10px] text-[var(--text-muted)] truncate mt-0.5">{p.evidence_data.technologies?.slice(0, 3).join(" · ")}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Experience — 2 sütun */}
      {topExp.length > 0 && (
        <section>
          <label className="block text-[11px] font-semibold tracking-wider uppercase mb-1.5 text-[var(--text-muted)]">Experience</label>
          <div className="grid grid-cols-2 gap-1.5">
            {topExp.map((e) => (
              <div key={e.id} className="px-2.5 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-medium text-[var(--text-primary)] truncate">{e.evidence_data.role || e.name}</span>
                  <Check className="h-3 w-3 text-[var(--success)] shrink-0 ml-auto" />
                </div>
                <p className="text-[10px] text-[var(--text-muted)] truncate mt-0.5">
                  {[e.evidence_data?.company, e.evidence_data?.duration].filter(Boolean).join(" · ")}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <button onClick={onComplete} className="w-full py-2 px-6 rounded-lg text-sm font-semibold tracking-wide transition-all" style={{ background: "var(--accent)", color: "var(--accent-fg)", cursor: "pointer" }}>
        Continue
      </button>
    </div>
  );
}
