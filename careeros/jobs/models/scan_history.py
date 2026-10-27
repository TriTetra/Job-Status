"""Scan history model — per-job scan tracking for trend analysis."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class ScanHistory(Base, TimestampMixin):
    """
    Records every scan a job appeared in.
    Enables: "this job was 85pts last week, 92pts now" and discovery-date tracking.
    """

    __tablename__ = "scan_history"

    url: Mapped[str] = mapped_column(String(2048), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, default=datetime.utcnow
    )

    applypilot_score: Mapped[int | None] = mapped_column(Integer)
    career_os_score: Mapped[float | None] = mapped_column(Float)

    # True only in the scan where this job first appeared
    discovered_in_this_scan: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_sh_url", "url"),
        Index("idx_sh_time", "scanned_at"),
        Index("idx_sh_discovered", "discovered_in_this_scan"),
        Index("idx_scan_history_user", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScanHistory url={self.url[:60]}... "
            f"scanned_at={self.scanned_at} new={self.discovered_in_this_scan}>"
        )
