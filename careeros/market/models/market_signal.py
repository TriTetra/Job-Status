"""Market signal — funding, layoffs, hiring spikes, skill trends."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class MarketSignal(Base, TimestampMixin):
    __tablename__ = "market_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    impact: Mapped[str] = mapped_column(String(20), default="medium")

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    companies_affected: Mapped[list] = mapped_column(ARRAY(String), default=list)
    skills_affected: Mapped[list] = mapped_column(ARRAY(String), default=list)
    countries_affected: Mapped[list] = mapped_column(ARRAY(String), default=list)

    magnitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Unique ID from source for deduplication
    source_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, unique=True)

    __table_args__ = (
        Index("idx_market_signals_type", "signal_type"),
        Index("idx_market_signals_source", "source"),
        Index("idx_market_signals_impact", "impact"),
        Index("idx_market_signals_occurred", "occurred_at"),
        Index("idx_market_signals_companies", "companies_affected", postgresql_using="gin"),
        Index("idx_market_signals_skills", "skills_affected", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<MarketSignal({self.signal_type}: {self.title[:50]})>"
