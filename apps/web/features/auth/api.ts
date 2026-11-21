import { apiFetch } from "@/lib/api/client";

import type { CreatedInvite, Invite, Me, NewAccount } from "./types";

const json = (body: unknown) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<void>("/api/auth/login", { method: "POST", ...json({ email, password }) }),
  logout: () => apiFetch<void>("/api/auth/logout", { method: "POST" }),
  me: () => apiFetch<Me>("/api/auth/me"),

  // First account (only while the site has none)
  setupStatus: () => apiFetch<{ needed: boolean }>("/api/auth/setup"),
  setup: (account: NewAccount) => apiFetch<void>("/api/auth/setup", { method: "POST", ...json(account) }),

  // Invite links
  checkInvite: (token: string) =>
    apiFetch<{ valid: boolean; email: string | null }>("/api/auth/invites/check", {
      method: "POST",
      ...json({ token }),
    }),
  acceptInvite: (token: string, account: NewAccount) =>
    apiFetch<void>("/api/auth/invites/accept", { method: "POST", ...json({ token, ...account }) }),
  listInvites: () => apiFetch<Invite[]>("/api/auth/invites"),
  createInvite: (email?: string) =>
    apiFetch<CreatedInvite>("/api/auth/invites", { method: "POST", ...json({ email: email || null }) }),
  revokeInvite: (id: string) => apiFetch<void>(`/api/auth/invites/${encodeURIComponent(id)}`, { method: "DELETE" }),

  changePassword: (current_password: string, new_password: string) =>
    apiFetch<void>("/api/auth/password", { method: "POST", ...json({ current_password, new_password }) }),
};

/** FastAPI's {"detail": "..."} as a sentence for the user, or null. */
export function apiDetail(body: string): string | null {
  try {
    const detail = JSON.parse(body)?.detail;
    return typeof detail === "string" ? detail : null;
  } catch {
    return null;
  }
}
