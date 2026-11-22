import { apiFetch } from "@/lib/api/client";

/** Hide a briefing to-do for a week. */
export const dismissTodo = (key: string) =>
  apiFetch<{ status: string }>("/api/briefing/dismiss", { method: "POST", body: JSON.stringify({ key }) });
