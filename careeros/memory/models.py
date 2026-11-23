"""person_events (the log) and job_impressions (what was shown, at which rank)."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (BigInteger, Date, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class PersonEvent(Base):
    """One thing that happened with the person: intent, who said it, and two clocks.

    Never updated in place. `actor` separates the person's own statements ("user") from
    inferences ("agent:<name>") and imports ("import:<source>"); a user correction wins.
    `valid_from` is when it became true in the person's life; `recorded_at` when Aplio learned it.
    """

    __tablename__ = "person_events"
    __table_args__ = (
        UniqueConstraint("user_id", "stream", "stream_version", name="uq_person_events_stream_version"),
        Index("idx_person_events_user_time", "user_id", "recorded_at"),
        Index("idx_person_events_user_type", "user_id", "type"),
    )

    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stream: Mapped[str] = mapped_column(String(160), nullable=False)  # profile | job:<id> | application:<id> | cv | evidence
    stream_version: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_ver: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, default="user")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_ref: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    causation_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class JobImpression(Base):
    """A job shown to the person on a surface, once per day (best rank kept). Without it,
    "didn't see" and "didn't want" look the same to anything that learns from decisions."""

    __tablename__ = "job_impressions"

    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), primary_key=True)
    surface: Mapped[str] = mapped_column(String(16), primary_key=True)  # inbox | search
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    best_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    times: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
