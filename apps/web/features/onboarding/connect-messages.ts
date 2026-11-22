import { ApiError } from "@/lib/api/client";
import { apiDetail } from "@/features/auth/api";

export type Notice = { tone: "ok" | "error" | "muted"; text: string };

/** The `?github=` outcome the API redirects back with, as a sentence. */
const GITHUB_NOTICES: Record<string, Notice> = {
  connected: {
    tone: "ok",
    text: "GitHub connected. Your repositories are being read in the background; their languages and projects join your evidence in a minute.",
  },
  cancelled: { tone: "muted", text: "GitHub connection cancelled." },
  error: { tone: "error", text: "GitHub couldn't be connected. Try again." },
  unavailable: { tone: "muted", text: "GitHub isn't set up on this site yet. The admin needs to add a GitHub OAuth app." },
};

/** The sentence for `?github=<outcome>`, or null. */
export function githubNotice(outcome: string | null): Notice | null {
  return outcome ? GITHUB_NOTICES[outcome] ?? null : null;
}

/** Why a portfolio / profile couldn't be read — the API's own sentence when it sent one. */
export function crawlErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 422) return "Check what you entered and try again.";
    return apiDetail(err.body) ?? "It could not be read. Try again.";
  }
  return "Couldn't reach the server. Try again.";
}

export function crawlSummary(r: { projects_found: number; technologies_found: number; pages_read?: number }): string {
  const pages = r.pages_read && r.pages_read > 1 ? ` across ${r.pages_read} pages` : "";
  if (!r.projects_found && !r.technologies_found) {
    return `Read the site${pages}, but found no projects or technologies on it.`;
  }
  return `Found ${r.projects_found} project${r.projects_found === 1 ? "" : "s"} and ${r.technologies_found} technolog${r.technologies_found === 1 ? "y" : "ies"}${pages}.`;
}

export const NOTICE_COLOR: Record<Notice["tone"], string> = {
  ok: "var(--success)",
  error: "var(--danger)",
  muted: "var(--text-muted)",
};
