import { listBoardCompanies } from "@/features/companies/board-server";
import { CompaniesView } from "./_components/companies-view";

export default async function CompaniesPage() {
  return <CompaniesView companies={await listBoardCompanies()} />;
}
