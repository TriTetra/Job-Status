"""Application repository — pipeline status queries."""

from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import func, select

from careeros.applications.models.application import Application
from careeros.db.repository import BaseRepository


STATUSES = ("to_apply", "applied", "interview", "offer", "rejected", "withdrawn", "skipped")
# Moves that are the employer's answer: what the chance model will learn from
OUTCOMES = {"interview": "interview", "offer": "offer", "rejected": "reject"}
SENT = ("applied", "interview", "offer")


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
        cv = self._cv(user_id) if status in SENT else None
        app = self.create(user_id=user_id, url=url, title=title, company=company, status=status, notes=notes,
                          applied_at=now if status in SENT else None, history=[_event(status, now)],
                          resume_version=cv["ref"] if cv else None)
        self._remember(app, None, status, cv)
        return app

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
        before = obj.status
        kwargs: dict = {"status": status, "history": [*(obj.history or []), _event(status, at)]}
        cv = None
        user_id = getattr(obj, "user_id", None)
        if status in SENT and obj.applied_at is None:
            kwargs["applied_at"] = at
            cv = self._cv(user_id) if user_id else None
            if cv and not getattr(obj, "resume_version", None):
                kwargs["resume_version"] = cv["ref"]  # the CV that was current when it was sent
        app = self.update(obj, **kwargs)
        if user_id:
            self._remember(app, before, status, cv, at)
        return app

    def _cv(self, user_id: str) -> dict | None:
        from careeros.memory.cv import current_cv

        try:
            return current_cv(self.session, user_id)
        except Exception:
            return None

    def _remember(self, app: Application, before: str | None, status: str, cv: dict | None,
                  at: datetime | None = None) -> None:
        """One event per move: the employer's answer as OutcomeObserved, anything else as a stage change."""
        from careeros.memory.events import job_stream, remember

        payload = {"url": app.url, "title": app.title, "company": app.company, "from": before, "to": status}
        if cv:
            payload["cv"] = cv
        if status in OUTCOMES:
            remember(self.session, app.user_id, "OutcomeObserved", {**payload, "kind": OUTCOMES[status]},
                     stream=job_stream(app.url), valid_from=at)
        else:
            remember(self.session, app.user_id, "ApplicationStageChanged", payload, stream=job_stream(app.url),
                     valid_from=at)

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
