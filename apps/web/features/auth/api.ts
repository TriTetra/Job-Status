import { apiFetch } from "@/lib/api/client";

import type { Me } from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<void>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  logout: () => apiFetch<void>("/api/auth/logout", { method: "POST" }),
  me: () => apiFetch<Me>("/api/auth/me"),
};
