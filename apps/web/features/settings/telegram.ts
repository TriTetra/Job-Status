import { apiFetch } from "@/lib/api/client";

/** GET /api/telegram (careeros/notifications/links.py::status). */
export interface TelegramStatus {
  /** The server has a bot token (TELEGRAM_BOT_TOKEN) */
  available: boolean;
  bot: string | null;
  connected: boolean;
  username: string | null;
  linked_at: string | null;
  prefs: { matches: boolean; reminders: boolean };
}

export const telegramApi = {
  status: () => apiFetch<TelegramStatus>("/api/telegram"),
  link: () => apiFetch<{ url: string }>("/api/telegram/link", { method: "POST" }),
  prefs: (prefs: Partial<TelegramStatus["prefs"]>) =>
    apiFetch<{ prefs: TelegramStatus["prefs"] }>("/api/telegram/prefs", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    }),
  test: () => apiFetch<void>("/api/telegram/test", { method: "POST" }),
  disconnect: () => apiFetch<void>("/api/telegram", { method: "DELETE" }),
};
