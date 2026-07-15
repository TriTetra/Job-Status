import type { OnboardingState } from "./types";

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

export const GOALS = [
  { id: "salary", label: "Maximizing Salary" },
  { id: "remote", label: "Remote Flexibility" },
  { id: "growth", label: "Career Growth" },
  { id: "balance", label: "Work-life Balance" },
  { id: "prestige", label: "Company Prestige" },
  { id: "learning", label: "Learning Opportunities" },
];

export const COUNTRIES: { name: string; region: string }[] = [
  // North America
  { name: "United States",          region: "North America" },
  { name: "Canada",                 region: "North America" },
  { name: "Mexico",                 region: "North America" },
  // Europe
  { name: "Germany",                region: "Europe" },
  { name: "United Kingdom",         region: "Europe" },
  { name: "France",                 region: "Europe" },
  { name: "Netherlands",            region: "Europe" },
  { name: "Switzerland",            region: "Europe" },
  { name: "Sweden",                 region: "Europe" },
  { name: "Norway",                 region: "Europe" },
  { name: "Denmark",                region: "Europe" },
  { name: "Finland",                region: "Europe" },
  { name: "Spain",                  region: "Europe" },
  { name: "Portugal",               region: "Europe" },
  { name: "Italy",                  region: "Europe" },
  { name: "Poland",                 region: "Europe" },
  { name: "Austria",                region: "Europe" },
  { name: "Belgium",                region: "Europe" },
  { name: "Ireland",                region: "Europe" },
  { name: "Czech Republic",         region: "Europe" },
  { name: "Romania",                region: "Europe" },
  { name: "Hungary",                region: "Europe" },
  { name: "Ukraine",                region: "Europe" },
  // Middle East
  { name: "United Arab Emirates",   region: "Middle East" },
  { name: "Saudi Arabia",           region: "Middle East" },
  { name: "Turkey",                 region: "Middle East" },
  { name: "Israel",                 region: "Middle East" },
  { name: "Qatar",                  region: "Middle East" },
  { name: "Kuwait",                 region: "Middle East" },
  // Central Asia
  { name: "Uzbekistan",             region: "Central Asia" },
  { name: "Kazakhstan",             region: "Central Asia" },
  { name: "Azerbaijan",             region: "Central Asia" },
  { name: "Georgia",                region: "Central Asia" },
  // Asia Pacific
  { name: "Singapore",              region: "Asia Pacific" },
  { name: "Japan",                  region: "Asia Pacific" },
  { name: "South Korea",            region: "Asia Pacific" },
  { name: "Australia",              region: "Asia Pacific" },
  { name: "New Zealand",            region: "Asia Pacific" },
  { name: "India",                  region: "Asia Pacific" },
  { name: "China",                  region: "Asia Pacific" },
  { name: "Hong Kong",              region: "Asia Pacific" },
  { name: "Taiwan",                 region: "Asia Pacific" },
  { name: "Vietnam",                region: "Asia Pacific" },
  { name: "Indonesia",              region: "Asia Pacific" },
  { name: "Thailand",               region: "Asia Pacific" },
  { name: "Malaysia",               region: "Asia Pacific" },
  { name: "Philippines",            region: "Asia Pacific" },
  // Latin America
  { name: "Brazil",                 region: "Latin America" },
  { name: "Argentina",              region: "Latin America" },
  { name: "Colombia",               region: "Latin America" },
  { name: "Chile",                  region: "Latin America" },
  // Africa
  { name: "South Africa",           region: "Africa" },
  { name: "Nigeria",                region: "Africa" },
  { name: "Kenya",                  region: "Africa" },
  { name: "Egypt",                  region: "Africa" },
];

export const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "TRY"];

