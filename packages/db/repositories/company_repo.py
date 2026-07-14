"""Company and CompanyMemory repositories."""

from datetime import datetime
from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import Company, CompanyMemory
from .base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def get_or_create(self, name: str) -> Company:
        company = self.get(name=name)
        if company:
            return company
        return self.create(name=name, tier="unknown")

    def get_by_tier(self, tier: str) -> List[Company]:
        stmt = (
            sa.select(self.model)
            .where(self.model.tier == tier)
            .order_by(self.model.name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_all(self) -> List[Company]:
        stmt = sa.select(self.model).order_by(self.model.tier, self.model.name)
        return list(self.session.execute(stmt).scalars().all())

    def get_hiring_now(self, limit: int = 20) -> List[Company]:
        stmt = (
            sa.select(self.model)
            .where(self.model.hiring_trend.in_(["up", "spike"]))
            .where(self.model.open_positions_count > 0)
            .order_by(self.model.open_positions_count.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def find_by_tech_stack(self, skills: List[str], limit: int = 10) -> List[Company]:
        """Find companies whose tech_stack contains ALL given skills (JSONB @>)."""
        stmt = (
            sa.select(self.model)
            .where(self.model.tech_stack.op("@>")(sa.cast(skills, JSONB)))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_tech_stack(self, name: str, tech_stack: List[str]) -> Company:
        company = self.get_or_create(name)
        existing = set(company.tech_stack or [])
        existing.update(tech_stack)
        company.tech_stack = list(existing)
        company.last_enriched = datetime.utcnow()
        company.enrichment_source = "job_postings"
        return company


# Need JSONB cast
from sqlalchemy.dialects.postgresql import JSONB


class CompanyMemoryRepository(BaseRepository[CompanyMemory]):
    model = CompanyMemory

    def add_fact(
        self,
        user_id: str,
        company_name: str,
        fact_type: str,
        fact_data: dict,
        occurred_at: Optional[datetime] = None,
        confidence: float = 1.0,
        source: str = "manual",
    ) -> CompanyMemory:
        return self.create(
            user_id=user_id,
            company_name=company_name,
            fact_type=fact_type,
            fact_data=fact_data,
            occurred_at=occurred_at or datetime.utcnow(),
            confidence=confidence,
            source=source,
        )

    def get_facts_for_company(self, user_id: str, company_name: str) -> List[CompanyMemory]:
        stmt = (
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.company_name == company_name)
            .order_by(self.model.occurred_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_application_outcomes(self, user_id: str, company_name: str) -> List[dict]:
        stmt = (
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.company_name == company_name)
            .where(self.model.fact_type == "application_outcome")
            .order_by(self.model.occurred_at.desc())
        )
        return [r.fact_data for r in self.session.execute(stmt).scalars().all()]

    def get_company_summary(self, user_id: str, company_name: str) -> dict:
        facts = self.get_facts_for_company(user_id, company_name)
        if not facts:
            return {"total_interactions": 0}

        outcomes = [f for f in facts if f.fact_type == "application_outcome"]
        interview_topics = [f for f in facts if f.fact_type == "interview_topic"]

        return {
            "total_interactions": len(facts),
            "application_count": len(outcomes),
            "rejection_count": sum(
                1 for o in outcomes if o.fact_data.get("outcome") == "rejected"
            ),
            "interview_count": sum(
                1 for o in outcomes
                if o.fact_data.get("stage") in {"phone_screen", "technical", "onsite"}
            ),
            "offer_count": sum(
                1 for o in outcomes if o.fact_data.get("outcome") == "offer"
            ),
            "interview_topics_asked": list({
                topic
                for t in interview_topics
                for topic in t.fact_data.get("topics", [])
            }),
        }
