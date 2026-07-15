import type { OnboardingState } from "./types";

// ─── Step Metadata ────────────────────────────────────────────────────────────

export const STEP_META: Record<
  Exclude<OnboardingState, "NOT_STARTED" | "READY">,
  { label: string; description: string }
> = {
  IDENTITY: {
    label: "About you",
    description: "Tell us who you are and where you are in your career.",
  },
  GOALS: {
    label: "Your goals",
    description: "Define the roles and industries you're targeting.",
  },
  EVIDENCE: {
    label: "Your evidence",
    description: "Connect your GitHub, resume, or past work.",
  },
  CONNECTIONS: {
    label: "Your network",
    description: "Import contacts and map your professional network.",
  },
  BUILDING: {
    label: "Build your profile",
    description: "We'll compile everything into your career narrative.",
  },
};

export const STEP_ORDER: Exclude<OnboardingState, "NOT_STARTED" | "READY">[] = [
  "IDENTITY",
  "GOALS",
  "EVIDENCE",
  "CONNECTIONS",
  "BUILDING",
];

// ─── Goals ────────────────────────────────────────────────────────────────────

export interface GoalOption {
  id: string;
  label: string;
  icon: string;
}

export interface GoalCategory {
  name: string;
  maxSelections: number;
  goals: GoalOption[];
}

export const GOAL_CATEGORIES: GoalCategory[] = [
  {
    name: "Career Growth",
    maxSelections: 2,
    goals: [
      { id: "technical_depth", label: "Technical Depth", icon: "🔬" },
      { id: "leadership", label: "Leadership", icon: "👑" },
      { id: "management", label: "Management", icon: "📊" },
      { id: "research", label: "Research", icon: "🔭" },
    ],
  },
  {
    name: "Work Style",
    maxSelections: 2,
    goals: [
      { id: "remote_first", label: "Remote First", icon: "🌍" },
      { id: "flexibility", label: "Flexibility", icon: "🕐" },
      { id: "balance", label: "Work-life Balance", icon: "⚖️" },
    ],
  },
  {
    name: "Company Preference",
    maxSelections: 2,
    goals: [
      { id: "startup", label: "Startup", icon: "🚀" },
      { id: "enterprise", label: "Enterprise", icon: "🏢" },
      { id: "big_tech", label: "Big Tech", icon: "⭐" },
      { id: "mission", label: "Mission Driven", icon: "🌱" },
    ],
  },
  {
    name: "Compensation",
    maxSelections: 1,
    goals: [
      { id: "high_salary", label: "High Salary", icon: "💰" },
      { id: "equity", label: "Equity", icon: "📈" },
      { id: "benefits", label: "Benefits", icon: "🎁" },
    ],
  },
  {
    name: "Impact",
    maxSelections: 2,
    goals: [
      { id: "open_source", label: "Open Source", icon: "💻" },
      { id: "innovation", label: "Innovation", icon: "⚡" },
      { id: "social_impact", label: "Social Impact", icon: "🌍" },
    ],
  },
];

export const TOTAL_GOALS_LIMIT = 5;

// ─── Work Arrangements ────────────────────────────────────────────────────────

export const WORK_ARRANGEMENTS = [
  { id: "remote", label: "Remote", icon: "🌍" },
  { id: "hybrid", label: "Hybrid", icon: "🏢" },
  { id: "onsite", label: "On-site", icon: "🏭" },
] as const;

// ─── Countries (ISO codes) ────────────────────────────────────────────────────

export interface Country {
  code: string;
  name: string;
  region: string;
}

export const COUNTRIES: Country[] = [
  // North America
  { code: "US", name: "United States", region: "North America" },
  { code: "CA", name: "Canada", region: "North America" },
  { code: "MX", name: "Mexico", region: "North America" },
  // Europe
  { code: "DE", name: "Germany", region: "Europe" },
  { code: "GB", name: "United Kingdom", region: "Europe" },
  { code: "FR", name: "France", region: "Europe" },
  { code: "NL", name: "Netherlands", region: "Europe" },
  { code: "CH", name: "Switzerland", region: "Europe" },
  { code: "SE", name: "Sweden", region: "Europe" },
  { code: "NO", name: "Norway", region: "Europe" },
  { code: "DK", name: "Denmark", region: "Europe" },
  { code: "FI", name: "Finland", region: "Europe" },
  { code: "ES", name: "Spain", region: "Europe" },
  { code: "PT", name: "Portugal", region: "Europe" },
  { code: "IT", name: "Italy", region: "Europe" },
  { code: "PL", name: "Poland", region: "Europe" },
  { code: "AT", name: "Austria", region: "Europe" },
  { code: "BE", name: "Belgium", region: "Europe" },
  { code: "IE", name: "Ireland", region: "Europe" },
  { code: "CZ", name: "Czech Republic", region: "Europe" },
  { code: "EE", name: "Estonia", region: "Europe" },
  { code: "RO", name: "Romania", region: "Europe" },
  { code: "HU", name: "Hungary", region: "Europe" },
  { code: "UA", name: "Ukraine", region: "Europe" },
  // Middle East
  { code: "AE", name: "United Arab Emirates", region: "Middle East" },
  { code: "SA", name: "Saudi Arabia", region: "Middle East" },
  { code: "TR", name: "Turkey", region: "Middle East" },
  { code: "IL", name: "Israel", region: "Middle East" },
  { code: "QA", name: "Qatar", region: "Middle East" },
  // Central Asia
  { code: "UZ", name: "Uzbekistan", region: "Central Asia" },
  { code: "KZ", name: "Kazakhstan", region: "Central Asia" },
  { code: "AZ", name: "Azerbaijan", region: "Central Asia" },
  { code: "GE", name: "Georgia", region: "Central Asia" },
  // Asia Pacific
  { code: "SG", name: "Singapore", region: "Asia Pacific" },
  { code: "JP", name: "Japan", region: "Asia Pacific" },
  { code: "KR", name: "South Korea", region: "Asia Pacific" },
  { code: "AU", name: "Australia", region: "Asia Pacific" },
  { code: "NZ", name: "New Zealand", region: "Asia Pacific" },
  { code: "IN", name: "India", region: "Asia Pacific" },
  { code: "CN", name: "China", region: "Asia Pacific" },
  { code: "HK", name: "Hong Kong", region: "Asia Pacific" },
  { code: "TW", name: "Taiwan", region: "Asia Pacific" },
  { code: "VN", name: "Vietnam", region: "Asia Pacific" },
  { code: "ID", name: "Indonesia", region: "Asia Pacific" },
  { code: "TH", name: "Thailand", region: "Asia Pacific" },
  { code: "MY", name: "Malaysia", region: "Asia Pacific" },
  { code: "PH", name: "Philippines", region: "Asia Pacific" },
  // Latin America
  { code: "BR", name: "Brazil", region: "Latin America" },
  { code: "AR", name: "Argentina", region: "Latin America" },
  { code: "CO", name: "Colombia", region: "Latin America" },
  { code: "CL", name: "Chile", region: "Latin America" },
  // Africa
  { code: "ZA", name: "South Africa", region: "Africa" },
  { code: "NG", name: "Nigeria", region: "Africa" },
  { code: "KE", name: "Kenya", region: "Africa" },
  { code: "EG", name: "Egypt", region: "Africa" },
];

export const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "CHF", "SEK", "TRY", "SGD", "AUD"] as const;

// ─── Legacy (step-identity.tsx still uses these) ──────────────────────────────

export const GOALS = [
  { id: "salary", label: "Maximizing Salary" },
  { id: "remote", label: "Remote Flexibility" },
  { id: "growth", label: "Career Growth" },
  { id: "balance", label: "Work-life Balance" },
  { id: "prestige", label: "Company Prestige" },
  { id: "learning", label: "Learning Opportunities" },
];
