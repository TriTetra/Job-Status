"use client";

import { useState } from "react";
import { NarrativeText } from "@/components/shared/narrative-text";
import { Button } from "@/components/shared/button";
import { OpportunityItem, OpportunityFeed } from "@/components/ui/opportunity-item";
import { Search, SlidersHorizontal, Zap } from "lucide-react";

type FilterRec = "ALL" | "APPLY" | "CONSIDER" | "SKIP";

interface MockOpportunity {
  id: string;
  score: number;
  recommendation: "APPLY" | "CONSIDER" | "SKIP";
  company: { name: string; tier: string };
  role: string;
  location: string;
  remote?: boolean;
  visaSponsorship?: boolean;
  deadline?: string;
  matchedSkills: { name: string; confidence: number }[];
  gapSkills: string[];
  whyHighlights: string[];
  breakdown: { label: string; value: number; positive: boolean; description?: string }[];
}

const MOCK_OPPORTUNITIES: MockOpportunity[] = [
  {
    id: "1",
    score: 87,
    recommendation: "APPLY" as const,
    company: { name: "Stripe", tier: "Unicorn" },
    role: "Backend Engineer",
    location: "Remote",
    remote: true,
    visaSponsorship: true,
    deadline: "5 days",
    matchedSkills: [
      { name: "Rust", confidence: 82 },
      { name: "Go", confidence: 75 },
      { name: "Kubernetes", confidence: 70 },
    ],
    gapSkills: ["Kafka"],
    whyHighlights: [
      "Strong Rust match (+28)",
      "Unicorn tier matches preference (+12)",
      "Remote fits your preference (+8)",
    ],
    breakdown: [
      { label: "Rust experience", value: 28, positive: true, description: "You: 82%, they need: high" },
      { label: "Kubernetes", value: 15, positive: true },
      { label: "OSS activity", value: 12, positive: true },
      { label: "Unicorn tier", value: 10, positive: true },
      { label: "Missing Kafka", value: -8, positive: false },
    ],
  },
  {
    id: "2",
    score: 82,
    recommendation: "APPLY" as const,
    company: { name: "Anthropic", tier: "Unicorn" },
    role: "Research Engineer",
    location: "San Francisco, CA",
    visaSponsorship: true,
    matchedSkills: [
      { name: "PyTorch", confidence: 78 },
      { name: "Research", confidence: 85 },
    ],
    gapSkills: ["Distributed systems"],
    whyHighlights: [
      "Research publications match (+22)",
      "PyTorch expertise (+18)",
      "Mission-aligned (AI safety)",
    ],
    breakdown: [
      { label: "Research background", value: 22, positive: true },
      { label: "PyTorch", value: 18, positive: true },
      { label: "Unicorn tier", value: 10, positive: true },
      { label: "SF onsite preference", value: -5, positive: false },
      { label: "Distributed systems gap", value: -8, positive: false },
    ],
  },
  {
    id: "3",
    score: 76,
    recommendation: "APPLY" as const,
    company: { name: "Databricks", tier: "Unicorn" },
    role: "Senior Data Engineer",
    location: "Remote (EU)",
    remote: true,
    visaSponsorship: true,
    matchedSkills: [
      { name: "Python", confidence: 92 },
      { name: "Spark", confidence: 65 },
    ],
    gapSkills: ["Scala", "Delta Lake"],
    whyHighlights: [
      "Python expertise (+20)",
      "Data engineering focus matches (+15)",
    ],
    breakdown: [
      { label: "Python expertise", value: 20, positive: true },
      { label: "Data engineering", value: 15, positive: true },
      { label: "Remote EU", value: 8, positive: true },
      { label: "Missing Scala", value: -10, positive: false },
      { label: "Missing Delta Lake", value: -7, positive: false },
    ],
  },
  {
    id: "4",
    score: 68,
    recommendation: "CONSIDER" as const,
    company: { name: "Google", tier: "Big Tech" },
    role: "ML Engineer",
    location: "Mountain View, CA",
    visaSponsorship: true,
    matchedSkills: [
      { name: "TensorFlow", confidence: 60 },
      { name: "Python", confidence: 92 },
    ],
    gapSkills: ["JAX", "TPU optimization"],
    whyHighlights: [
      "Python expertise (+20)",
      "Big Tech career value (+15)",
    ],
    breakdown: [
      { label: "Python expertise", value: 20, positive: true },
      { label: "Big Tech career value", value: 15, positive: true },
      { label: "TensorFlow", value: 12, positive: true },
      { label: "Missing JAX", value: -10, positive: false },
      { label: "Missing TPU opt", value: -8, positive: false },
      { label: "Competition", value: -5, positive: false },
    ],
  },
];

export default function InboxPage() {
  const [filter, setFilter] = useState<FilterRec>("ALL");
  const [search, setSearch] = useState("");

  const filtered = MOCK_OPPORTUNITIES.filter((o) => {
    if (filter !== "ALL" && o.recommendation !== filter) return false;
    if (search) {
      const q = search.toLowerCase();
      return o.company.name.toLowerCase().includes(q) || o.role.toLowerCase().includes(q);
    }
    return true;
  });

  const counts = {
    ALL:     MOCK_OPPORTUNITIES.length,
    APPLY:   MOCK_OPPORTUNITIES.filter((o) => o.recommendation === "APPLY").length,
    CONSIDER:MOCK_OPPORTUNITIES.filter((o) => o.recommendation === "CONSIDER").length,
    SKIP:    MOCK_OPPORTUNITIES.filter((o) => o.recommendation === "SKIP").length,
  };

  return (
    <div className="wide-container px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <NarrativeText size="2xl" weight="semibold" className="mb-1">
            Opportunities
          </NarrativeText>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {counts.ALL} total · {counts.APPLY} ready to apply · Updated 2h ago
          </p>
        </div>
        <Button variant="primary" size="md">
          <Zap className="h-4 w-4" />
          Scan Now
        </Button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center gap-3 flex-wrap">
        <div
          className="flex items-center gap-1 p-1 rounded-lg"
          style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
        >
          {(["ALL", "APPLY", "CONSIDER", "SKIP"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
              style={{
                background: filter === f ? "rgba(255,177,98,0.15)" : "transparent",
                color: filter === f ? "var(--accent)" : "var(--text-secondary)",
              }}
            >
              {f} ({counts[f]})
            </button>
          ))}
        </div>

        <div className="flex-1 min-w-[200px] max-w-sm relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
            strokeWidth={1.75}
            style={{ color: "var(--text-muted)" }}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search company or role..."
            className="w-full h-9 pl-9 pr-3 rounded-lg text-sm outline-none transition-colors"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
            }}
          />
        </div>

        <button
          className="h-9 px-3 rounded-lg text-sm inline-flex items-center gap-2 transition-colors"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <SlidersHorizontal className="h-4 w-4" strokeWidth={1.75} />
          Filters
        </button>
      </div>

      {/* Feed */}
      {filtered.length > 0 ? (
        <OpportunityFeed>
          {filtered.map((opp) => (
            <OpportunityItem
              key={opp.id}
              score={opp.score}
              recommendation={opp.recommendation}
              company={opp.company}
              role={opp.role}
              location={opp.location}
              remote={opp.remote}
              visaSponsorship={opp.visaSponsorship}
              deadline={opp.deadline}
              matchedSkills={opp.matchedSkills}
              gapSkills={opp.gapSkills}
              whyHighlights={opp.whyHighlights}
              breakdown={opp.breakdown}
            />
          ))}
        </OpportunityFeed>
      ) : (
        <div className="surface p-12 text-center">
          <NarrativeText size="lg" weight="medium" className="mb-2">
            No opportunities match your filters
          </NarrativeText>
          <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
            Try adjusting your filters or scanning for new jobs.
          </p>
          <Button variant="outline" onClick={() => { setFilter("ALL"); setSearch(""); }}>
            Clear filters
          </Button>
        </div>
      )}
    </div>
  );
}
