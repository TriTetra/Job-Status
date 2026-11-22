import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import type { Application, ApplicationAnalytics } from "./api";

export const listApplications = () => serverApiFetch<Application[]>("/api/applications/");

export const getApplicationAnalytics = () => serverApiFetch<ApplicationAnalytics>("/api/applications/analytics");
