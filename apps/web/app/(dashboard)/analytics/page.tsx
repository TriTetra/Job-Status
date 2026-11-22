import { getApplicationAnalytics } from "@/features/applications/server";
import { AnalyticsView } from "./_components/analytics-view";

export default async function AnalyticsPage() {
  return <AnalyticsView a={await getApplicationAnalytics()} />;
}
