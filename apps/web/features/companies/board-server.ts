import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import type { BoardCompany, BoardCompanyDetail } from "./board-types";

export const listBoardCompanies = async () =>
  (await serverApiFetch<{ companies: BoardCompany[] }>("/api/companies/boards")).companies;

export const getBoardCompany = (key: string) =>
  serverApiFetch<BoardCompanyDetail>(`/api/companies/boards/${encodeURIComponent(key)}`);
