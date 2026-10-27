"""Scan history repository."""

from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy import select

from careeros.jobs.models.scan_history import ScanHistory
from careeros.db.repository import BaseRepository


class ScanHistoryRepository(BaseRepository[ScanHistory]):

    model = ScanHistory

    def record_scan(
        self,
        url: str,
        applypilot_score: int | None,
        career_os_score: float | None,
        discovered_in_this_scan: bool,
        scanned_at: datetime | None = None,
        user_id: str = "default",
    ) -> ScanHistory:
        return self.create(
            user_id=user_id,
            url=url,
            scanned_at=scanned_at or datetime.utcnow(),
            applypilot_score=applypilot_score,
            career_os_score=career_os_score,
            discovered_in_this_scan=discovered_in_this_scan,
        )

    def get_first_seen(self, url: str, user_id: str = "default") -> Optional[datetime]:
        stmt = (
            select(self.model.scanned_at)
            .where(self.model.user_id == user_id)
            .where(self.model.url == url)
            .where(self.model.discovered_in_this_scan.is_(True))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_urls_seen_in_scan(self, scanned_at: datetime, user_id: str = "default") -> List[str]:
        """All job URLs that appeared in a specific scan timestamp."""
        stmt = (
            select(self.model.url)
            .where(self.model.user_id == user_id)
            .where(self.model.scanned_at == scanned_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_new_this_scan(self, scanned_at: datetime, user_id: str = "default") -> List[ScanHistory]:
        """Jobs discovered for the first time in a given scan."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.scanned_at == scanned_at)
            .where(self.model.discovered_in_this_scan.is_(True))
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_all_known_urls(self, user_id: str = "default") -> Set[str]:
        """All job URLs ever seen across all scans for this user."""
        stmt = (
            select(self.model.url)
            .where(self.model.user_id == user_id)
            .distinct()
        )
        return set(self.session.execute(stmt).scalars().all())
