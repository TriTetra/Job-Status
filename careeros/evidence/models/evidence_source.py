"""EvidenceSource — metadata-driven connection registry (no hardcoded sources)."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from careeros.db.base import Base


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), server_default="coming_soon")
    oauth_provider: Mapped[str | None] = mapped_column(String(50))
    connect_kind: Mapped[str] = mapped_column(String(20), server_default="oauth")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
