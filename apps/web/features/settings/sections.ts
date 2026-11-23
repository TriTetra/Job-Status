import { Gauge, KeyRound, Plug, SlidersHorizontal, UserRound, type LucideIcon } from "lucide-react";

/** Settings is a dialog over the current page, opened with ?settings=<section>. */
export const SECTIONS = [
  { id: "profile", label: "Profile", icon: UserRound, blurb: "Who you are. It shapes every score, suggestion and resume." },
  { id: "preferences", label: "Preferences", icon: SlidersHorizontal, blurb: "Where and how you want to work, and how your briefing talks to you." },
  { id: "scoring", label: "Scoring", icon: Gauge, blurb: "What matters most when Aplio ranks a role for you." },
  { id: "connections", label: "Connections", icon: Plug, blurb: "Telegram notifications, and where your proof comes from: code, writing, talks, papers." },
  { id: "account", label: "Account", icon: KeyRound, blurb: "How you sign in, and who you invite." },
] as const satisfies ReadonlyArray<{ id: string; label: string; icon: LucideIcon; blurb: string }>;

export type SectionId = (typeof SECTIONS)[number]["id"];

export const SETTINGS_PARAM = "settings";

export function parseSection(value: string | null | undefined): SectionId | null {
  if (value == null) return null;
  return SECTIONS.find((s) => s.id === value)?.id ?? "profile";
}

/** Old /settings?tab= links (briefing to-dos, GitHub's return): the account tab held the proof sources. */
export function legacyTab(tab: string | undefined): SectionId {
  return tab === "account" ? "connections" : parseSection(tab ?? "profile") ?? "profile";
}

/** The current URL with the settings dialog open on `section` (other query params kept). */
export function settingsHref(section: SectionId = "profile", base?: { pathname: string; search: string }): string {
  const { pathname, search } = base ?? window.location;
  const q = new URLSearchParams(search);
  q.set(SETTINGS_PARAM, section);
  return `${pathname}?${q}`;
}
