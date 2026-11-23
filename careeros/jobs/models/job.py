"""Job model — every posting CareerOS knows about, from company boards or imports."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    """
    Single source of truth for job listings, shared by all users.
    Board syncs (careeros/jobs/ingest.py) upsert here; scans score from here;
    career_scores joins back on url.
    """

    __tablename__ = "jobs"

    url: Mapped[str] = mapped_column(String(2048), primary_key=True)

    # Core metadata
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    company: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Where it came from: a company board (company_key + ats) or an import (site)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="applypilot")
    site: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    company_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ats: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    company_domain: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)   # employer website (logo)
    company_logo: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)    # logo URL a feed provides
    # A job a person added themselves (careeros/jobs/added.py): only they see it. NULL = shared.
    added_by: Mapped[Optional[str]] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"),
                                                    nullable=True)

    # External scanner score (ApplyPilot imports only)
    fit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Normalized fields (careeros/jobs/extraction.py)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    required_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    remote: Mapped[Optional[bool]] = mapped_column(nullable=True)
    remote_region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sponsors_visa: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # None = not stated
    required_skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # LLM-extracted facts (careeros/jobs/llm_extract.py), valid while llm_facts_hash == content_hash
    llm_facts: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    llm_facts_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Lifecycle. content_hash changes when the posting text does → rescore.
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # first seen
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def visible_to(user_id: Optional[str]):
        """Shared jobs, plus the ones this person added themselves (never anyone else's)."""
        from sqlalchemy import or_

        return Job.added_by.is_(None) if not user_id else or_(Job.added_by.is_(None), Job.added_by == user_id)

    __table_args__ = (
        Index("idx_jobs_company", "company"),
        Index("idx_jobs_site", "site"),
        Index("idx_jobs_source", "source"),
        Index("idx_jobs_fit_score", "fit_score"),
        Index("idx_jobs_discovered_at", "discovered_at"),
        Index("idx_jobs_skills_gin", "required_skills", postgresql_using="gin"),
        Index("idx_jobs_company_key", "company_key"),
        Index("idx_jobs_open", "discovered_at", postgresql_where="closed_at IS NULL"),
        Index("idx_jobs_added_by", "added_by", postgresql_where="added_by IS NOT NULL"),
    )

    def __repr__(self) -> str:
        return f"<Job url={self.url[:60]}... title={self.title[:40]}>"
