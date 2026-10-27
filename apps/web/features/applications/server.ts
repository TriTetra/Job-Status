import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import type { Application } from "./api";

export const listApplications = () => serverApiFetch<Application[]>("/api/applications/");
