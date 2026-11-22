import type { Application, ApplicationStatus } from "./api";

export const STAGES: Array<{ id: ApplicationStatus; label: string; hint: string; next?: { to: ApplicationStatus; label: string } }> = [
  { id: "to_apply", label: "To apply", hint: "Shortlisted, not sent yet", next: { to: "applied", label: "I applied" } },
  { id: "applied", label: "Applied", hint: "Waiting to hear back", next: { to: "interview", label: "Got an interview" } },
  { id: "interview", label: "Interview", hint: "In conversation", next: { to: "offer", label: "Got an offer" } },
  { id: "offer", label: "Offer", hint: "Your decision" },
];

export const STATUS_LABEL: Record<string, string> = {
  to_apply: "Shortlisted",
  applied: "Applied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  skipped: "Passed",
};

export function host(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export const companyOf = (a: Pick<Application, "company" | "url">) => a.company || host(a.url);

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function daysLabel(days: number | null): string {
  if (days == null) return "";
  return days <= 0 ? "today" : days === 1 ? "1 day" : `${days} days`;
}

/** How long it has sat in its stage, in that stage's words. */
export function ageLine(a: Application): string {
  const d = daysLabel(a.days_in_status);
  if (!d) return "";
  switch (a.status) {
    case "to_apply": return a.days_in_status! <= 0 ? "shortlisted today" : `shortlisted ${d} ago`;
    case "applied": return a.days_in_status! <= 0 ? "sent today" : `waiting ${d}`;
    case "interview": return `interviewing · ${d}`;
    case "offer": return a.days_in_status! <= 0 ? "offer today" : `offer · ${d}`;
    default: return `${STATUS_LABEL[a.status].toLowerCase()} ${shortDate(a.updated_at)}`;
  }
}

export const REC_COLOR: Record<string, string> = { APPLY: "var(--success)", CONSIDER: "var(--accent)", SKIP: "var(--text-muted)" };
