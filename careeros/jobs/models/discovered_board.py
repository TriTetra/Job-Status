"""Company job boards found through job feeds (careeros/jobs/discovery.py), read like companies.yaml."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class DiscoveredBoard(Base):
    __tablename__ = "discovered_boards"
    __table_args__ = (UniqueConstraint("ats", "board", name="uq_discovered_boards_ats_board"),)

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    ats: Mapped[str] = mapped_column(String(32), nullable=False)
    board: Mapped[str] = mapped_column(String(256), nullable=False)
    host: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    domain: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False)          # feed that pointed at it
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # failed reads in a row
