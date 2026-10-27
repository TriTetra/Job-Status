import { listApplications } from "@/features/applications/server";
import { ApplicationsView } from "./_components/applications-view";

export default async function ApplicationsPage() {
  return <ApplicationsView initialApps={await listApplications()} />;
}
