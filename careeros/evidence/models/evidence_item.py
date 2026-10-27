"""EvidenceItem model — per-skill proof linked to a source (resume, GitHub, etc.)."""

from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class EvidenceItem(Base, TimestampMixin):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    skill_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    skill_name: Mapped[str] = mapped_column(String(150), nullable=False)

    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    evidence_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    resume_document_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("resume_documents.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("idx_evidence_items_user_skill", "user_id", "skill_name"),
        Index("idx_evidence_items_confidence", "confidence_score"),
    )
