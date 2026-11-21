import { Brand } from "../../_components/brand";
import { InviteForm } from "./invite-form";

export default async function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <div className="w-full max-w-md">
      <Brand />
      <InviteForm token={token} />
    </div>
  );
}
