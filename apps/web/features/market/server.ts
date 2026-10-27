import "server-only";

import { serverApiFetch } from "@/lib/api/server";

import { DEFAULT_RANGE, loadMarketSnapshot } from "./snapshot";

export const getInitialMarket = () => loadMarketSnapshot(serverApiFetch, DEFAULT_RANGE);
