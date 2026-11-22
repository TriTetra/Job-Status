import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import { DEFAULT_PERIOD, loadMarket } from "./snapshot";

export const getInitialMarket = () => loadMarket(serverApiFetch, DEFAULT_PERIOD);
