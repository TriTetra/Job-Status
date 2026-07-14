"""Candidate Memory — user learning patterns and application history analysis."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sqlalchemy as sa

from core.db.connection import db
from core.db.models import Application

from .base import BaseMemory, MemoryFact


class CandidateMemory(BaseMemory):
    """
    Stores user learning patterns derived from application outcomes.

    In-memory for now; DB persistence is a future extension.
    """

    def __init__(self, user_id: str = "default"):
        super().__init__(user_id)
        self._facts: List[MemoryFact] = []

    def add_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        expires_after_days: Optional[int] = None,
    ) -> MemoryFact:
        expires_at = None
        if expires_after_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_after_days)

        fact = MemoryFact(
            fact_type=fact_type,
            content=content,
            confidence=confidence,
            metadata=metadata or {},
            expires_at=expires_at,
            source=source,
        )
        self._facts.append(fact)
        return fact

    def get_facts(
        self,
        fact_type: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[MemoryFact]:
        facts = self._facts
        if not include_expired:
            facts = [f for f in facts if not f.is_expired()]
        if fact_type:
            facts = [f for f in facts if f.fact_type == fact_type]
        return sorted(facts, key=lambda f: f.created_at, reverse=True)[:limit]

    def clear(self):
        self._facts.clear()

    def learn_from_application_outcome(
        self,
        company: str,
        stage: str,
        outcome: str,
        job_title: str = "",
    ) -> None:
        if outcome == "rejected":
            self.add_fact(
                fact_type="rejection_pattern",
                content=f"Rejected at {company} ({stage}) for {job_title}",
                confidence=0.7,
                metadata={"company": company, "stage": stage, "job_title": job_title},
                source="application_outcome",
            )
        elif outcome == "offer":
            self.add_fact(
                fact_type="success_pattern",
                content=f"Received offer from {company} for {job_title}",
                confidence=1.0,
                metadata={"company": company, "job_title": job_title},
                source="application_outcome",
            )

    def analyze_remote_vs_onsite(self) -> Dict[str, Any]:
        with db.session_scope() as session:
            stmt = sa.select(Application).where(Application.user_id == self.user_id)
            applications = list(session.execute(stmt).scalars().all())

        remote_apps = [a for a in applications if "remote" in (a.notes or "").lower()]
        onsite_apps = [a for a in applications if a not in remote_apps]

        interview_stages = {"phone_screen", "technical", "onsite"}
        remote_interviews = [a for a in remote_apps if a.status in interview_stages]
        onsite_interviews = [a for a in onsite_apps if a.status in interview_stages]

        remote_rate = len(remote_interviews) / len(remote_apps) if remote_apps else 0.0
        onsite_rate = len(onsite_interviews) / len(onsite_apps) if onsite_apps else 0.0

        if remote_rate > onsite_rate * 1.5:
            recommendation = "prefer_remote"
        elif onsite_rate > remote_rate * 1.5:
            recommendation = "prefer_onsite"
        else:
            recommendation = "neutral"

        return {
            "remote_application_count": len(remote_apps),
            "remote_interview_count": len(remote_interviews),
            "remote_interview_rate": remote_rate,
            "onsite_application_count": len(onsite_apps),
            "onsite_interview_count": len(onsite_interviews),
            "onsite_interview_rate": onsite_rate,
            "recommendation": recommendation,
        }

    def get_learning_preferences(self) -> Dict[str, Any]:
        return {
            "preferred_format": "project",
            "optimal_hours_per_week": 10,
            "preferred_time_of_day": "evening",
        }
