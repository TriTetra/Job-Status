"""Visa entity — visa types and requirements, seeded from YAML, editable via UI."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Visa(Base, TimestampMixin):
    __tablename__ = "visas"

    visa_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    category: Mapped[str] = mapped_column(String(30), default="work_permit")

    description: Mapped[Optional[str]] = mapped_column(String(1000))
    duration: Mapped[Optional[str]] = mapped_column(String(200))
    path_to_pr: Mapped[Optional[str]] = mapped_column(String(200))
    family_reunification: Mapped[bool] = mapped_column(Boolean, default=True)

    eligibility: Mapped[dict] = mapped_column(JSONB, default=dict)
    application: Mapped[dict] = mapped_column(JSONB, default=dict)
    alternatives: Mapped[dict] = mapped_column(JSONB, default=dict)
    pros: Mapped[list] = mapped_column(JSONB, default=list)
    cons: Mapped[list] = mapped_column(JSONB, default=list)
    best_for: Mapped[list] = mapped_column(JSONB, default=list)

    last_updated_by: Mapped[Optional[str]] = mapped_column(String(100))
    last_updated_at: Mapped[Optional[datetime]] = mapped_column()
    data_source: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("idx_visas_country", "country"),
        Index("idx_visas_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<Visa({self.visa_type})>"
