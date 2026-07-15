export type EmphasisTone = "primary" | "accent" | "success";

export interface TextSegment {
  text: string;
  emphasis?: EmphasisTone;
}

export interface BriefingGreeting {
  name: string;
}

/** One sentence in the Brief section, built from emphasized segments */
export interface BriefLine {
  segments: TextSegment[];
  muted?: boolean;
}

export interface FocusItem {
  number: "01" | "02" | "03";
  action: string;
  reason: string;
  ctaLabel: string;
  ctaHref?: string;
}

export type Recommendation = "APPLY" | "CONSIDER" | "SKIP";

export interface Opportunity {
  id: string;
  company: string;
  role: string;
  location: string;
  score: number;
  recommendation: Recommendation;
  why: string[];
  gap?: string;
}

export interface EvidenceSignal {
  text: string;
}

export interface EvidenceSummary {
  signalCount: number;
  signals: EvidenceSignal[];
  confidence: "High" | "Medium" | "Low";
}

export interface ProgressSummary {
  headline: string;
  attribution: string;
  promise: string;
  ctaLabel?: string;
  ctaHref?: string;
}

export interface ClosingCopy {
  lines: string[];
}

export interface BriefingData {
  greeting: BriefingGreeting;
  brief: BriefLine[];
  focus: FocusItem[];
  opportunities: Opportunity[];
  evidence: EvidenceSummary;
  progress: ProgressSummary;
  closing: ClosingCopy;
}

export interface BriefingEmptyData {
  watching: string[];
}

/** Discriminated union so the page can render the ready or empty narrative cleanly */
export type BriefingResult =
  | { status: "ready"; data: BriefingData }
  | { status: "empty"; data: BriefingEmptyData };
