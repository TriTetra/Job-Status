import { apiFetch } from "@/lib/api/client";

import type { BoardCompanyDetail } from "./board-types";

export const fetchBoardCompany = (key: string) =>
  apiFetch<BoardCompanyDetail>(`/api/companies/boards/${encodeURIComponent(key)}`);
