import type { MarketData, MarketSignal, OwnMarket, PayByCountry, Period } from "./types";

type Get = <T>(path: string) => Promise<T>;

export const DEFAULT_PERIOD: Period = 30;

/** Own-market numbers + recent news. `get` is serverApiFetch or apiFetch; news failing is not fatal. */
export async function loadMarket(get: Get, days: Period): Promise<MarketData> {
  const [own, news, pay] = await Promise.all([
    get<OwnMarket>(`/api/market/jobs?days=${days}`),
    get<MarketSignal[]>(`/api/market/signals?days=${days}&limit=12`).catch(() => [] as MarketSignal[]),
    get<PayByCountry>("/api/market/pay").catch(() => null),
  ]);
  return { own, news, pay };
}
