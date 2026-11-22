"""Application repository — pipeline status queries."""

from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import func, select

from careeros.applications.models.application import Application
from careeros.db.repository import BaseRepository


STATUSES = ("to_apply", "applied", "interview", "offer", "rejected", "withdrawn", "skipped")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event(status: str, at: datetime) -> dict:
    return {"status": status, "at": at.astimezone(timezone.utc).isoformat(timespec="seconds")}


class ApplicationRepository(BaseRepository[Application]):

    model = Application

    def upsert(
        self,
        url: str,
        title: str,
        company: str | None = None,
        status: str = "to_apply",
        user_id: str = "default",
        notes: str | None = None,
    ) -> Application:
        """Insert if not exists for this user, else return existing."""
        existing = self._get_for_user(url=url, user_id=user_id)
        if existing:
            return existing
        now = _now()
        return self.create(user_id=user_id, url=url, title=title, company=company, status=status, notes=notes,
                           applied_at=now if status in ("applied", "interview", "offer") else None,
                           history=[_event(status, now)])

    def mark_applied(
        self, url: str, applied_at: datetime | None = None, user_id: str = "default"
    ) -> Optional[Application]:
        obj = self._get_for_user(url=url, user_id=user_id)
        if not obj:
            return None
        return self._move(obj, "applied", at=applied_at)

    def advance_status(
        self, url: str, new_status: str, notes: str | None = None, user_id: str = "default"
    ) -> Optional[Application]:
        obj = self._get_for_user(url=url, user_id=user_id)
        if not obj:
            return None
        if notes is not None:
            obj.notes = notes or None
        return self._move(obj, new_status)

    def set_notes(self, url: str, notes: str | None, user_id: str = "default") -> Optional[Application]:
        obj = self._get_for_user(url=url, user_id=user_id)
        if not obj:
            return None
        return self.update(obj, notes=(notes or "").strip() or None)

    def remove(self, url: str, user_id: str = "default") -> bool:
        obj = self._get_for_user(url=url, user_id=user_id)
        if not obj:
            return False
        self.delete(obj)
        return True

    def _move(self, obj: Application, status: str, at: datetime | None = None) -> Application:
        """Change status, log it in history, stamp applied_at the first time it is applied."""
        if status == obj.status:
            return obj
        at = at or _now()
        kwargs: dict = {"status": status, "history": [*(obj.history or []), _event(status, at)]}
        if status in ("applied", "interview", "offer") and obj.applied_at is None:
            kwargs["applied_at"] = at
        return self.update(obj, **kwargs)

    def get_by_status(self, status: str, user_id: str = "default") -> List[Application]:
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.status == status)
            .order_by(self.model.updated_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_pipeline_summary(self, user_id: str = "default") -> dict[str, int]:
        """{'to_apply': 12, 'applied': 5, 'interview': 2, ...}"""
        rows = self.session.execute(
            select(self.model.status, func.count().label("n"))
            .where(self.model.user_id == user_id)
            .group_by(self.model.status)
        ).all()
        return {row.status: row.n for row in rows}

    def get_stale(
        self, statuses: List[str], before: datetime, user_id: str = "default"
    ) -> List[Application]:
        """Jobs in `statuses` whose updated_at is older than `before`."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.status.in_(statuses))
            .where(self.model.updated_at < before)
            .order_by(self.model.updated_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_for_user(self, url: str, user_id: str) -> Optional[Application]:
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.url == url)
        )
        return self.session.execute(stmt).scalar_one_or_none()
