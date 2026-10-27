"""Career score repository — one row per (user, job), upserted by scans."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from careeros.db.repository import BaseRepository
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job

_SCORE_FIELDS = (
    "career_score", "fit_score", "acceptance_probability", "career_value", "market_demand",
    "expected_value", "recommendation", "skill_gaps", "explanation", "input_hash",
)


class CareerScoreRepository(BaseRepository[CareerScore]):

    model = CareerScore

    def upsert_score(self, user_id: str, url: str, scanned_at: Optional[datetime] = None, **fields) -> None:
        """Insert or replace the user's score for a job; first_scored_at survives rescoring."""
        now = scanned_at or datetime.utcnow()
        values = {k: fields[k] for k in _SCORE_FIELDS if k in fields}
        values.setdefault("skill_gaps", [])
        values.setdefault("explanation", {})
        stmt = pg_insert(CareerScore).values(user_id=user_id, url=url, scanned_at=now, first_scored_at=now, **values)
        self.session.execute(stmt.on_conflict_do_update(
            index_elements=["user_id", "url"],
            set_={**{k: stmt.excluded[k] for k in values}, "scanned_at": now, "updated_at": func.now()},
        ))

    def input_hashes(self, user_id: str) -> dict[str, Optional[str]]:
        rows = self.session.execute(
            select(CareerScore.url, CareerScore.input_hash).where(CareerScore.user_id == user_id)
        ).all()
        return dict(rows)

    def get_latest_score(self, url: str, user_id: str) -> Optional[CareerScore]:
        return self.session.get(CareerScore, (user_id, url))

    def _open(self, stmt, user_id: str):
        """The user's scores whose job is still open (or was never tracked in `jobs`)."""
        return (
            stmt.select_from(CareerScore)
            .outerjoin(Job, Job.url == CareerScore.url)
            .where(CareerScore.user_id == user_id, Job.closed_at.is_(None))
        )

    def get_top_opportunities(
        self,
        min_score: Optional[float] = 60.0,
        recommendation: Optional[str] = "APPLY",
        limit: int = 20,
        user_id: str = "",
        recommendations: Optional[tuple[str, ...]] = None,
    ) -> List[CareerScore]:
        """Open opportunities, best first. None for min_score/recommendation = no filter.

        Recommendations match as a prefix: rows scored before normalization store the
        scorer's full text ("APPLY - Strong opportunity").
        """
        stmt = self._open(select(CareerScore), user_id).order_by(CareerScore.career_score.desc()).limit(limit)
        if min_score is not None:
            stmt = stmt.where(CareerScore.career_score >= min_score)
        wanted = recommendations or ((recommendation,) if recommendation else ())
        if wanted:
            stmt = stmt.where(or_(*(CareerScore.recommendation.startswith(r) for r in wanted)))
        return list(self.session.execute(stmt).scalars().all())

    def count_latest(self, user_id: str, recommendation: Optional[str] = None) -> int:
        """How many open jobs the user has a score for (optionally in one recommendation bucket)."""
        stmt = self._open(select(func.count()), user_id)
        if recommendation is not None:
            stmt = stmt.where(CareerScore.recommendation.startswith(recommendation))
        return self.session.execute(stmt).scalar_one()
