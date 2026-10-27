"""Career score model — per-scan scoring results stored as time series."""

from datetime import datetime
from sqlalchemy import Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class CareerScore(Base, TimestampMixin):
    """
    Every scan inserts a new row (url, scanned_at) composite PK.
    user_id isolates rows per user; existing rows default to 'default'.
    """

    __tablename__ = "career_scores"

    url: Mapped[str] = mapped_column(String(2048), primary_key=True)
    scanned_at: Mapped[datetime] = mapped_column(primary_key=True, default=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")

    # Scores (0–100)
    career_score: Mapped[float] = mapped_column(Float, nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    acceptance_probability: Mapped[float] = mapped_column(Float, nullable=False)
    career_value: Mapped[float] = mapped_column(Float, nullable=False)
    market_demand: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)

    # APPLY | CONSIDER | SKIP (full text from OpportunityScorer)
    recommendation: Mapped[str] = mapped_column(String(100), nullable=False)

    # JSONB: native indexing, not TEXT blobs
    skill_gaps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    explanation: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_cs_url", "url"),
        Index("idx_cs_time", "scanned_at"),
        Index("idx_cs_recommendation", "recommendation"),
        Index("idx_cs_career_score", "career_score"),
        Index("idx_cs_skill_gaps_gin", "skill_gaps", postgresql_using="gin"),
        Index("idx_career_scores_user", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CareerScore url={self.url[:60]}... "
            f"score={self.career_score:.1f} rec={self.recommendation}>"
        )
