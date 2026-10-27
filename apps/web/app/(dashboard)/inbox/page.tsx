import { getInbox } from "@/features/opportunities/server";
import { InboxView } from "./_components/inbox-view";

export default async function InboxPage() {
  return <InboxView initial={await getInbox()} />;
}
