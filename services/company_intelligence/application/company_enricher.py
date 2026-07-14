"""Populate Company table from knowledge YAML and job postings."""

from datetime import datetime
from typing import Dict, List

from packages.db.connection import db
from packages.db.repositories import CompanyRepository
from packages.knowledge import CompanyLoader


class CompanyEnricher:
    def __init__(self):
        self.knowledge = CompanyLoader()

    def seed_from_knowledge(self) -> int:
        companies = self.knowledge.load_all()

        with db.session_scope() as session:
            repo = CompanyRepository(session)
            seeded = 0

            for name, info in companies.items():
                company = repo.get_or_create(name)

                company.canonical_name = info.get("canonical_name")
                company.tier = info.get("tier", "unknown")
                company.industry = info.get("industry")
                company.headquarters = info.get("headquarters")
                company.employee_count = info.get("employee_count")

                new_tech = info.get("tech_stack", [])
                existing = set(company.tech_stack or [])
                existing.update(new_tech)
                company.tech_stack = list(existing)

                company.interview_rounds = info.get("interview_rounds", [])
                company.salary_ranges = info.get("salary_ranges", {})
                company.culture_signals = info.get("culture_signals", [])
                company.red_flags = info.get("red_flags", [])

                visa = info.get("visa_sponsorship") or info.get("sponsors_visa", False)
                company.sponsors_visa = bool(visa) and str(visa).lower() not in {"mostly", "false"}
                company.remote_friendly = bool(info.get("remote_friendly", True))

                company.last_enriched = datetime.utcnow()
                company.enrichment_source = "knowledge_yaml"
                seeded += 1

            return seeded

    def enrich_from_job_postings(self, jobs: List[dict]) -> Dict[str, int]:
        by_company: Dict[str, List[dict]] = {}
        for job in jobs:
            company = job.get("company")
            if company and company != "Unknown":
                by_company.setdefault(company, []).append(job)

        with db.session_scope() as session:
            repo = CompanyRepository(session)
            processed: Dict[str, int] = {}

            for company_name, company_jobs in by_company.items():
                all_skills: set = set()
                for job in company_jobs:
                    all_skills.update(job.get("required_skills", []))
                    all_skills.update(job.get("preferred_skills", []))

                repo.update_tech_stack(company_name, list(all_skills))

                company = repo.get_or_create(company_name)
                company.open_positions_count = len(company_jobs)

                processed[company_name] = len(company_jobs)

            return processed
