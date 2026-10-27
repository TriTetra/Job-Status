import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import type { Company } from "./types";

export const listCompanies = () => serverApiFetch<Company[]>("/api/companies/");
