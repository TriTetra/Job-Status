import type { BriefingResult } from "./types";

export const MOCK_BRIEFING: BriefingResult = {
  status: "ready",
  data: {
    greeting: { name: "Abdullokh" },

    brief: [
      { segments: [{ text: "Here's what changed while you were away." }] },
      {
        segments: [
          { text: "17 new opportunities", emphasis: "accent" },
          { text: " appeared overnight." },
        ],
      },
      {
        segments: [
          { text: "Anthropic", emphasis: "primary" },
          { text: " opened a new ML research team." },
        ],
      },
      {
        segments: [
          { text: "Rust demand climbed " },
          { text: "11%", emphasis: "success" },
          { text: " this week." },
        ],
      },
      { segments: [{ text: "That's the biggest change today." }], muted: true },
    ],

    focus: [
      {
        number: "01",
        action: "Apply to Stripe",
        reason: "Profile matches 91%. Deadline in 5 days.",
        ctaLabel: "Why strong?",
      },
      {
        number: "02",
        action: "Prepare for Google interview",
        reason: "Friday 2pm. Focus: system design.",
        ctaLabel: "Study plan",
      },
      {
        number: "03",
        action: "Learn Kafka this weekend",
        reason: "Unlocks 231 jobs. 14h. ROI 9.7.",
        ctaLabel: "Start",
      },
    ],

    opportunities: [
      {
        id: "anthropic",
        company: "Anthropic",
        role: "Research Engineer",
        location: "San Francisco",
        score: 91,
        recommendation: "APPLY",
        why: ["Research publications", "PyTorch expertise"],
        gap: "Distributed systems",
      },
      {
        id: "stripe",
        company: "Stripe",
        role: "Backend Engineer",
        location: "Remote",
        score: 87,
        recommendation: "APPLY",
        why: ["Strong Rust match", "Unicorn tier"],
        gap: "Kafka",
      },
    ],

    evidence: {
      signalCount: 3,
      signals: [
        { text: "Resume matches 91% of their requirements" },
        { text: "Recruiters opened your profile 8 times this week" },
        { text: "Rust demand climbed 11% in your target market" },
      ],
      confidence: "High",
    },

    progress: {
      headline: "You doubled your response rate.",
      attribution: "The biggest contributor appears to be Resume Version 7.",
      promise: "We'll continue measuring this.",
      ctaLabel: "See full analytics",
      ctaHref: "/analytics",
    },

    closing: {
      lines: [
        "That's everything important for today.",
        "We'll keep watching. See you tomorrow.",
      ],
    },
  },
};

export const MOCK_BRIEFING_EMPTY: BriefingResult = {
  status: "empty",
  data: {
    watching: [
      "3 companies you follow",
      "Rust demand trend (currently stable)",
      "Your pending applications",
    ],
  },
};
