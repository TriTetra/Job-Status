"""Evidence model — per-skill proof tracking from GitHub + CV evaluation."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Evidence(Base, TimestampMixin):
    """
    One row = one (skill, project) pair with a confidence score.

    Examples:
    - skill=Python,  project=Project-Drone-Vision, commits=15, stars=0, confidence=0.72
    - skill=YOLOv8,  project=Project-Drone-Vision, commits=15, stars=0, confidence=0.78
    - skill=Python,  project=everything-python,     commits=56, stars=0, confidence=0.81
    """

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(String(500))

    author_commits: Mapped[int] = mapped_column(Integer, default=0)
    stars: Mapped[int] = mapped_column(Integer, default=0)

    # 0.0–1.0
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Raw scores that fed into this confidence value
    evaluation_scores: Mapped[dict] = mapped_column(JSONB, default=dict)

    # github_project | production | certificate | hackathon
    evidence_type: Mapped[str] = mapped_column(
        String(50), default="github_project", nullable=False
    )

    # Real GitHub metrics (populated by Phase 3B enrichment)
    loc_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topics: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    pr_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_releases: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_tests: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_docs: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_commit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_evidence_skill", "skill_name"),
        Index("idx_evidence_project", "project_name"),
        Index("idx_evidence_confidence", "confidence"),
        Index("idx_evidence_user", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence skill={self.skill_name!r} "
            f"project={self.project_name!r} "
            f"confidence={self.confidence:.2f}>"
        )
