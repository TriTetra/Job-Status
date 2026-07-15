"use client";

import { cn } from "@/lib/utils";
import { NarrativeText } from "@/components/shared/narrative-text";
import { MetricText } from "@/components/shared/metric-text";
import { LabelText } from "@/components/shared/label-text";
import { SkillTag } from "./skill-tag";
import { Button } from "@/components/shared/button";
import {
  Github,
  GitCommit,
  Star,
  Code2,
  CheckCircle2,
  FileText,
  Package,
} from "lucide-react";

export interface EvidenceProject {
  name: string;
  githubUrl: string;
  commits: number;
  stars: number;
  loc: number;
  topics: string[];
  qualitySignals: {
    hasTests: boolean;
    hasDocs: boolean;
    hasReleases: boolean;
  };
  evidenceFor: string[];
  lastCommit?: string;
}

interface EvidenceSurfaceProps {
  skill: string;
  confidence: number;
  projectCount: number;
  totalCommits: number;
  totalStars: number;
  projects: EvidenceProject[];
  onUseInResume?: (projectName: string) => void;
  onViewOnGitHub?: (url: string) => void;
  className?: string;
}

function QualitySignal({
  has,
  label,
  Icon,
}: {
  has: boolean;
  label: string;
  Icon: typeof CheckCircle2;
}) {
  return (
    <span
      className={cn("inline-flex items-center gap-1 text-[11px]", has ? "" : "line-through")}
      style={{ color: has ? "var(--success)" : "var(--text-muted)" }}
    >
      <Icon className="h-3 w-3" strokeWidth={has ? 2 : 1.5} />
      {label}
    </span>
  );
}

function ProjectCard({
  project,
  onUseInResume,
  onViewOnGitHub,
}: {
  project: EvidenceProject;
  onUseInResume?: () => void;
  onViewOnGitHub?: () => void;
}) {
  return (
    <div
      className="border-t pt-4 mt-4 first:border-t-0 first:pt-0 first:mt-0"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <Github
            className="h-4 w-4 shrink-0"
            strokeWidth={1.75}
            style={{ color: "var(--text-muted)" }}
          />
          <NarrativeText size="base" weight="medium" className="truncate">
            {project.name}
          </NarrativeText>
        </div>
        {project.lastCommit && (
          <span className="text-[11px] shrink-0" style={{ color: "var(--text-muted)" }}>
            {project.lastCommit}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
        <span className="inline-flex items-center gap-1.5">
          <GitCommit className="h-3.5 w-3.5" strokeWidth={1.75} style={{ color: "var(--text-muted)" }} />
          <MetricText value={project.commits} size="sm" showTrendIcon={false} />
          <span style={{ color: "var(--text-muted)" }}>commits</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Star className="h-3.5 w-3.5" strokeWidth={1.75} style={{ color: "var(--text-muted)" }} />
          <MetricText value={project.stars} size="sm" showTrendIcon={false} />
          <span style={{ color: "var(--text-muted)" }}>stars</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Code2 className="h-3.5 w-3.5" strokeWidth={1.75} style={{ color: "var(--text-muted)" }} />
          <MetricText value={project.loc.toLocaleString()} size="sm" showTrendIcon={false} />
          <span style={{ color: "var(--text-muted)" }}>LOC</span>
        </span>
      </div>

      {project.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {project.topics.map((topic) => (
            <span
              key={topic}
              className="inline-flex h-5 px-2 rounded text-[11px]"
              style={{ color: "var(--text-muted)", background: "var(--surface-hover)" }}
            >
              {topic}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 mb-3">
        <QualitySignal has={project.qualitySignals.hasTests} label="tests" Icon={CheckCircle2} />
        <QualitySignal has={project.qualitySignals.hasDocs} label="docs" Icon={FileText} />
        <QualitySignal has={project.qualitySignals.hasReleases} label="releases" Icon={Package} />
      </div>

      {project.evidenceFor.length > 0 && (
        <div className="mb-4">
          <LabelText className="mb-1.5 block">Evidence for</LabelText>
          <div className="flex flex-wrap gap-1.5">
            {project.evidenceFor.map((skill) => (
              <SkillTag key={skill} name={skill} variant="matched" />
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onViewOnGitHub}>
          <Github className="h-3.5 w-3.5" />
          GitHub
        </Button>
        <Button variant="secondary" size="sm" onClick={onUseInResume}>
          Use in resume
        </Button>
      </div>
    </div>
  );
}

export function EvidenceSurface({
  skill,
  confidence,
  projectCount,
  totalCommits,
  totalStars,
  projects,
  onUseInResume,
  onViewOnGitHub,
  className,
}: EvidenceSurfaceProps) {
  const barColor =
    confidence >= 80
      ? "var(--success)"
      : confidence >= 60
      ? "var(--accent)"
      : "var(--text-muted)";

  return (
    <div className={cn("surface p-6", className)}>
      <div className="flex items-center justify-between mb-2">
        <NarrativeText size="xl" weight="semibold">{skill}</NarrativeText>
        <MetricText value={confidence} unit="%" size="xl" />
      </div>

      <div
        className="h-1 w-full rounded-full overflow-hidden mb-3"
        style={{ background: "var(--surface-hover)" }}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(confidence, 100)}%`, background: barColor }}
        />
      </div>

      <div
        className="flex items-center gap-4 text-sm mb-6 pb-6 border-b"
        style={{ color: "var(--text-secondary)", borderColor: "var(--border)" }}
      >
        <span><MetricText value={projectCount} size="sm" showTrendIcon={false} /> projects</span>
        <span><MetricText value={totalCommits} size="sm" showTrendIcon={false} /> commits</span>
        <span><MetricText value={totalStars} size="sm" showTrendIcon={false} /> stars</span>
      </div>

      <LabelText className="mb-2 block">Projects</LabelText>
      <div>
        {projects.map((project) => (
          <ProjectCard
            key={project.name}
            project={project}
            onUseInResume={() => onUseInResume?.(project.name)}
            onViewOnGitHub={() => onViewOnGitHub?.(project.githubUrl)}
          />
        ))}
      </div>
    </div>
  );
}
