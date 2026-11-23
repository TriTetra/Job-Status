import { apiFetch } from "@/lib/api/client";

/** What an employer's e-mail meant (careeros/applications/models/mail_signal.py). */
export type MailKind = "rejection" | "interview" | "offer" | "info_request" | "acknowledgment" | "other";

export interface MailSignal {
  id: number;
  url: string | null;
  company: string | null;
  title: string | null;
  received_at: string | null;
  from_domain: string;
  subject: string;
  kind: MailKind;
  confidence: number;
  evidence: string;
  /** applied: the application was moved · pending: waits for you · dismissed */
  state: "applied" | "pending" | "dismissed" | "noted";
  status_before: string | null;
  status_after: string | null;
}

/** GET /api/mail (careeros/applications/mail/account.py::status). */
export interface MailStatus {
  connected: boolean;
  email: string | null;
  host: string | null;
  last_checked: string | null;
  problem: string | null;
  pending: number;
  signals: MailSignal[];
}

export const KIND_LABEL: Record<MailKind, string> = {
  rejection: "Rejection",
  interview: "Interview invite",
  offer: "Offer",
  info_request: "They ask for something",
  acknowledgment: "Application received",
  other: "Other",
};

export const PROBLEM_LABEL: Record<string, string> = {
  sign_in_failed: "The mail server refused the sign-in. The app password may have been revoked: connect again.",
  read_failed: "The last check couldn't read the mailbox. It tries again at the next refresh.",
};

export const mailApi = {
  status: () => apiFetch<MailStatus>("/api/mail"),
  connect: (email: string, password: string, host?: string) =>
    apiFetch<MailStatus>("/api/mail/connect", {
      method: "POST",
      body: JSON.stringify({ email, password, host: host?.trim() || null }),
    }),
  check: () => apiFetch<MailStatus & { result: Record<string, number | string> }>("/api/mail/check", { method: "POST" }),
  resolve: (id: number, action: "confirm" | "dismiss", kind?: MailKind) =>
    apiFetch<MailSignal>(`/api/mail/signals/${id}`, { method: "POST", body: JSON.stringify({ action, kind: kind ?? null }) }),
  disconnect: () => apiFetch<void>("/api/mail", { method: "DELETE" }),
};
