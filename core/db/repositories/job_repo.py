"""Job repository — upsert and query for raw job listings."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models import Job
from .base import BaseRepository


class JobRepository(BaseRepository[Job]):

    model = Job

    def upsert(self, job_data: Dict[str, Any]) -> Job:
        """
        Insert or update a job by URL (ON CONFLICT DO UPDATE).
        Returns the upserted row.
        """
        stmt = (
            pg_insert(Job)
            .values(**job_data)
            .on_conflict_do_update(
                index_elements=["url"],
                set_={
                    k: job_data[k]
                    for k in job_data
                    if k not in ("url", "created_at")
                },
            )
            .returning(Job)
        )
        result = self.session.execute(stmt)
        return result.scalar_one()

    def upsert_many(self, jobs: List[Dict[str, Any]]) -> int:
        """Bulk upsert. Returns number of rows inserted/updated."""
        if not jobs:
            return 0
        stmt = (
            pg_insert(Job)
            .values(jobs)
            .on_conflict_do_update(
                index_elements=["url"],
                set_={
                    k: getattr(pg_insert(Job).excluded, k)
                    for k in jobs[0]
                    if k not in ("url", "created_at")
                },
            )
        )
        result = self.session.execute(stmt)
        return result.rowcount

    def get_by_url(self, url: str) -> Optional[Job]:
        stmt = select(self.model).where(self.model.url == url)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_source(self, source: str, limit: int = 100) -> List[Job]:
        stmt = (
            select(self.model)
            .where(self.model.source == source)
            .order_by(self.model.discovered_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_min_fit_score(self, min_score: float, limit: int = 200) -> List[Job]:
        stmt = (
            select(self.model)
            .where(self.model.fit_score >= min_score)
            .order_by(self.model.fit_score.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_unscored(self, limit: int = 100) -> List[Job]:
        """Jobs that have no entry in career_scores yet."""
        from ..models import CareerScore
        scored_urls = select(CareerScore.url).distinct().scalar_subquery()
        stmt = (
            select(self.model)
            .where(self.model.url.not_in(scored_urls))
            .order_by(self.model.fit_score.desc().nullslast())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def known_urls(self) -> set[str]:
        """Return all known job URLs as a set (for deduplication)."""
        rows = self.session.execute(select(self.model.url)).scalars().all()
        return set(rows)
