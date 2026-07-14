"""Living company profile — populated from YAML, job postings, and scrapers."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200), primary_key=True)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    tier: Mapped[str] = mapped_column(String(50), default="unknown")
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    tech_stack: Mapped[list] = mapped_column(JSONB, default=list)
    interview_rounds: Mapped[list] = mapped_column(JSONB, default=list)
    salary_ranges: Mapped[dict] = mapped_column(JSONB, default=dict)
    culture_signals: Mapped[list] = mapped_column(JSONB, default=list)
    red_flags: Mapped[list] = mapped_column(JSONB, default=list)

    hiring_trend: Mapped[str] = mapped_column(String(20), default="stable")
    open_positions_count: Mapped[int] = mapped_column(Integer, default=0)
    sponsors_visa: Mapped[bool] = mapped_column(Boolean, default=False)
    remote_friendly: Mapped[bool] = mapped_column(Boolean, default=True)

    last_enriched: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    enrichment_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_companies_tier", "tier"),
        Index("idx_companies_hiring_trend", "hiring_trend"),
        Index("idx_companies_tech_stack", "tech_stack", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Company(name={self.name}, tier={self.tier})>"
