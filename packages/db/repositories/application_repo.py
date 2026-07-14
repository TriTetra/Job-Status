"""Application repository — pipeline status queries."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select

from ..models import Application
from .base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):

    model = Application

    def upsert(
        self,
        url: str,
        title: str,
        company: str | None = None,
        status: str = "to_apply",
    ) -> Application:
        """Insert if not exists, else return existing (no overwrite)."""
        existing = self.get(url=url)
        if existing:
            return existing
        return self.create(url=url, title=title, company=company, status=status)

    def mark_applied(self, url: str, applied_at: datetime | None = None) -> Optional[Application]:
        obj = self.get(url=url)
        if not obj:
            return None
        return self.update(obj, status="applied", applied_at=applied_at or datetime.utcnow())

    def advance_status(self, url: str, new_status: str, notes: str | None = None) -> Optional[Application]:
        obj = self.get(url=url)
        if not obj:
            return None
        kwargs = {"status": new_status}
        if notes:
            kwargs["notes"] = notes
        return self.update(obj, **kwargs)

    def get_by_status(self, status: str) -> List[Application]:
        return self.get_all(status=status)

    def get_pipeline_summary(self) -> dict[str, int]:
        """{'to_apply': 12, 'applied': 5, 'interview': 2, ...}"""
        from sqlalchemy import func
        rows = self.session.execute(
            select(self.model.status, func.count().label("n"))
            .group_by(self.model.status)
        ).all()
        return {row.status: row.n for row in rows}

    def get_stale(self, statuses: List[str], before: datetime) -> List[Application]:
        """Jobs in `statuses` whose updated_at is older than `before`."""
        stmt = (
            select(self.model)
            .where(self.model.status.in_(statuses))
            .where(self.model.updated_at < before)
            .order_by(self.model.updated_at)
        )
        return list(self.session.execute(stmt).scalars().all())
