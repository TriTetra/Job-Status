"""Per-user application history and advice for each company."""

from typing import Dict, List, Optional

from packages.db.connection import db
from packages.db.repositories import CompanyMemoryRepository


class CompanyMemoryService:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    def record_application_outcome(
        self,
        company_name: str,
        stage: str,
        outcome: str,
        job_title: str = "",
        reason: Optional[str] = None,
    ) -> None:
        with db.session_scope() as session:
            repo = CompanyMemoryRepository(session)
            repo.add_fact(
                user_id=self.user_id,
                company_name=company_name,
                fact_type="application_outcome",
                fact_data={"stage": stage, "outcome": outcome,
                           "job_title": job_title, "reason": reason},
                source="application_tracking",
            )

    def record_interview_topics(
        self,
        company_name: str,
        topics: List[str],
        round_name: str = "technical",
    ) -> None:
        with db.session_scope() as session:
            repo = CompanyMemoryRepository(session)
            repo.add_fact(
                user_id=self.user_id,
                company_name=company_name,
                fact_type="interview_topic",
                fact_data={"topics": topics, "round": round_name},
                source="interview_notes",
            )

    def get_advice_for_company(self, company_name: str) -> Dict:
        with db.session_scope() as session:
            repo = CompanyMemoryRepository(session)
            summary = repo.get_company_summary(self.user_id, company_name)
            outcomes = repo.get_application_outcomes(self.user_id, company_name)

        return {
            "company": company_name,
            "summary": summary,
            "previous_outcomes": outcomes,
            "recommendation": self._generate_recommendation(summary, outcomes),
        }

    def _generate_recommendation(self, summary: dict, outcomes: List[dict]) -> str:
        if summary.get("total_interactions", 0) == 0:
            return "No previous history. Standard application process."

        rejections = summary.get("rejection_count", 0)
        offers = summary.get("offer_count", 0)

        if offers > 0:
            return f"You have {offers} previous offer(s) from this company. Strong relationship."
        if rejections >= 3:
            return (
                f"Rejected {rejections} times. Consider waiting 6+ months "
                f"or strengthening your profile first."
            )
        if rejections >= 1:
            stage = outcomes[0].get("stage", "unknown") if outcomes else "unknown"
            return (
                f"Previously rejected at {stage}. "
                f"Review what was asked and prepare specifically for that round."
            )
        return "Previous interactions recorded. Check details below."

    def get_topics_to_study(self, company_name: str) -> List[str]:
        with db.session_scope() as session:
            repo = CompanyMemoryRepository(session)
            facts = repo.get_facts_for_company(self.user_id, company_name)

        seen: set = set()
        unique: List[str] = []
        for fact in facts:
            if fact.fact_type == "interview_topic":
                for t in fact.fact_data.get("topics", []):
                    if t not in seen:
                        seen.add(t)
                        unique.append(t)
        return unique
