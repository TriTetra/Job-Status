"""Scan history repository."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from ..models import ScanHistory
from .base import BaseRepository


class ScanHistoryRepository(BaseRepository[ScanHistory]):

    model = ScanHistory

    def record_scan(
        self,
        url: str,
        applypilot_score: int | None,
        career_os_score: float | None,
        discovered_in_this_scan: bool,
        scanned_at: datetime | None = None,
    ) -> ScanHistory:
        return self.create(
            url=url,
            scanned_at=scanned_at or datetime.utcnow(),
            applypilot_score=applypilot_score,
            career_os_score=career_os_score,
            discovered_in_this_scan=discovered_in_this_scan,
        )

    def get_first_seen(self, url: str) -> Optional[datetime]:
        stmt = (
            select(self.model.scanned_at)
            .where(self.model.url == url)
            .where(self.model.discovered_in_this_scan.is_(True))
            .limit(1)
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        return row

    def get_urls_seen_in_scan(self, scanned_at: datetime) -> List[str]:
        """All job URLs that appeared in a specific scan timestamp."""
        stmt = select(self.model.url).where(self.model.scanned_at == scanned_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_new_this_scan(self, scanned_at: datetime) -> List[ScanHistory]:
        """Jobs discovered for the first time in a given scan."""
        stmt = (
            select(self.model)
            .where(self.model.scanned_at == scanned_at)
            .where(self.model.discovered_in_this_scan.is_(True))
        )
        return list(self.session.execute(stmt).scalars().all())
