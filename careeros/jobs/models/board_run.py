"""Outcome of the latest sync per company board — answers "is it working?"."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class JobBoardRun(Base):
    __tablename__ = "job_board_runs"

    company_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # None when the last run succeeded
    fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)   # postings on the board
    kept: Mapped[int] = mapped_column(Integer, nullable=False, default=0)      # after the title filter
    new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
