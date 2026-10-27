import { listCompanies } from "@/features/companies/server";
import { CompaniesView } from "./_components/companies-view";

export default async function CompaniesPage() {
  return <CompaniesView initialCompanies={await listCompanies()} />;
}
