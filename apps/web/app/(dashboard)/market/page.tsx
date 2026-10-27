import { getInitialMarket } from "@/features/market/server";
import { MarketView } from "./_components/market-view";

export default async function MarketPage() {
  return <MarketView initial={await getInitialMarket()} />;
}
