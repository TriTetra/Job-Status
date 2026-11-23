/**
 * Every sentence the briefing says, per "Briefing voice" (Settings → Preferences).
 * warm: a quiet colleague · direct: numbers first · analytical: deltas.
 */

import type { Tone } from "./facts";

export function timeGreeting(hour: number): string {
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

export function leadFor(tone: Tone, c: { newMatches: number; newStrong: number; todos: number; hasScores: boolean }): string {
  if (!c.hasScores) {
    return tone === "direct"
      ? "No matches yet — run the first scan."
      : tone === "analytical"
        ? "0 scored jobs. A scan maps your evidence against every open role."
        : "Nothing to compare yet. One scan and this page starts telling you what changed.";
  }
  if (c.newMatches === 0) {
    const rest = c.todos > 0 ? ` ${plural(c.todos, "thing")} to look at.` : "";
    return tone === "direct"
      ? `No new matches.${rest}`
      : tone === "analytical"
        ? `Δ matches: 0.${rest}`
        : `A quiet stretch — no new matches since your last visit.${rest}`;
  }
  const strong = c.newStrong > 0 ? `, ${c.newStrong} strong` : "";
  return tone === "direct"
    ? `${plural(c.newMatches, "new match", "new matches")}${strong}.`
    : tone === "analytical"
      ? `+${c.newMatches} matches${c.newStrong ? ` (+${c.newStrong} APPLY)` : ""} since last visit.`
      : `${plural(c.newMatches, "new match", "new matches")} since your last visit${c.newStrong ? `, ${c.newStrong} of them strong` : ""}.`;
}

export function closingFor(tone: Tone, hour: number, dow: number): string[] {
  if (tone === "direct") return ["That's it."];
  if (tone === "analytical") return ["End of briefing. Busy boards are read hourly."];
  if (dow === 5) return ["That's everything for this week.", "Enjoy your weekend — we'll keep reading the boards."];
  if (dow === 0) return ["Rest well tonight.", "Tomorrow is a fresh start."];
  if (hour >= 22 || hour < 5) return ["That's everything for today.", "Rest well. We'll keep watching."];
  return ["That's everything important for today.", "We'll keep watching. See you tomorrow."];
}
