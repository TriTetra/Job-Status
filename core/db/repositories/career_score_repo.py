"""Career score repository — domain queries on top of BaseRepository."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, select

from ..models import CareerScore
from .base import BaseRepository


class CareerScoreRepository(BaseRepository[CareerScore]):

    model = CareerScore

    def save_score(
        self,
        url: str,
        career_score: float,
        fit_score: float,
        acceptance_probability: float,
        career_value: float,
        market_demand: float,
        expected_value: float,
        recommendation: str,
        skill_gaps: list | None = None,
        explanation: dict | None = None,
        scanned_at: datetime | None = None,
        user_id: str = "default",
    ) -> CareerScore:
        return self.create(
            user_id=user_id,
            url=url,
            scanned_at=scanned_at or datetime.utcnow(),
            career_score=career_score,
            fit_score=fit_score,
            acceptance_probability=acceptance_probability,
            career_value=career_value,
            market_demand=market_demand,
            expected_value=expected_value,
            recommendation=recommendation,
            skill_gaps=skill_gaps or [],
            explanation=explanation or {},
        )

    def get_latest_score(self, url: str, user_id: str = "default") -> Optional[CareerScore]:
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.url == url)
            .order_by(self.model.scanned_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_history(self, url: str, limit: int = 10, user_id: str = "default") -> List[CareerScore]:
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.url == url)
            .order_by(self.model.scanned_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_top_opportunities(
        self,
        min_score: Optional[float] = 60.0,
        recommendation: Optional[str] = "APPLY",
        limit: int = 20,
        user_id: str = "default",
    ) -> List[CareerScore]:
        """Latest score per job URL, filtered and ranked. None for min_score/recommendation = no filter."""
        latest_subq = (
            select(
                self.model.url,
                func.max(self.model.scanned_at).label("latest_scan"),
            )
            .where(self.model.user_id == user_id)
            .group_by(self.model.url)
            .subquery()
        )

        stmt = (
            select(self.model)
            .join(
                latest_subq,
                and_(
                    self.model.url == latest_subq.c.url,
                    self.model.scanned_at == latest_subq.c.latest_scan,
                ),
            )
            .where(self.model.user_id == user_id)
            .order_by(self.model.career_score.desc())
            .limit(limit)
        )
        if min_score is not None:
            stmt = stmt.where(self.model.career_score >= min_score)
        if recommendation is not None:
            stmt = stmt.where(self.model.recommendation == recommendation)
        return list(self.session.execute(stmt).scalars().all())

    def get_trends(self, url: str, days: int = 30, user_id: str = "default") -> List[CareerScore]:
        """Score history over the last N days (oldest first)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.url == url)
            .where(self.model.scanned_at >= cutoff)
            .order_by(self.model.scanned_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())
