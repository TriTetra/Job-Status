"""Job model — raw job listings imported from external sources (ApplyPilot, etc.)."""

from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    """
    Single source of truth for all job listings.
    Jobs are imported from external scanners (ApplyPilot) and then scored
    by the pipeline — career_scores joins back here on url.
    """

    __tablename__ = "jobs"

    url: Mapped[str] = mapped_column(String(2048), primary_key=True)

    # Core metadata
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    company: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_description: Mapped[str] = mapped_column(Text, nullable=True)

    # Source info
    site: Mapped[str] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="applypilot")
    application_url: Mapped[str] = mapped_column(String(2048), nullable=True)

    # External scanner score
    fit_score: Mapped[float] = mapped_column(Float, nullable=True)
    score_reasoning: Mapped[str] = mapped_column(Text, nullable=True)

    # Normalized fields (populated by plugin adapter)
    salary_min: Mapped[int] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=True)
    required_years: Mapped[float] = mapped_column(Float, nullable=True)
    company_size: Mapped[str] = mapped_column(String(32), nullable=True)
    remote: Mapped[bool] = mapped_column(nullable=True)
    required_skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps from source
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_jobs_company", "company"),
        Index("idx_jobs_site", "site"),
        Index("idx_jobs_source", "source"),
        Index("idx_jobs_fit_score", "fit_score"),
        Index("idx_jobs_discovered_at", "discovered_at"),
        Index("idx_jobs_skills_gin", "required_skills", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Job url={self.url[:60]}... title={self.title[:40]}>"
