import Link from "next/link";
import { notFound, unstable_rethrow } from "next/navigation";
import { ApiError } from "@/lib/api/server";
import { getBoardCompany } from "@/features/companies/board-server";
import { CompanyPanel } from "@/components/companies/company-panel";

/** A company on its own page (links from Market and elsewhere); same panel as the Companies view. */
export default async function CompanyPage({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  let c;
  try {
    c = await getBoardCompany(decodeURIComponent(name));
  } catch (err) {
    unstable_rethrow(err);
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }
  return (
    <div className="lg:h-full flex flex-col w-full max-w-[1200px] mx-auto px-6 lg:px-8 pt-6 pb-5">
      <Link href="/companies" className="text-sm shrink-0" style={{ color: "var(--text-muted)" }}>← All companies</Link>
      <div className="mt-4 rounded-2xl border overflow-hidden lg:flex-1 lg:min-h-0" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <CompanyPanel c={c} />
      </div>
    </div>
  );
}
