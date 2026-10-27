"""Country entity — living country profiles, seeded from YAML, editable via UI."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class Country(Base, TimestampMixin):
    __tablename__ = "countries"

    iso_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capital: Mapped[Optional[str]] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    language: Mapped[Optional[str]] = mapped_column(String(50))
    english_proficiency: Mapped[str] = mapped_column(String(20), default="high")

    tech_hubs: Mapped[list] = mapped_column(JSONB, default=list)
    primary_visa: Mapped[Optional[str]] = mapped_column(String(50))
    salary_threshold_eur: Mapped[Optional[int]] = mapped_column(Integer)
    shortage_occupations: Mapped[list] = mapped_column(JSONB, default=list)
    visa_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    tax_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    work_culture: Mapped[dict] = mapped_column(JSONB, default=dict)
    pros: Mapped[list] = mapped_column(JSONB, default=list)
    cons: Mapped[list] = mapped_column(JSONB, default=list)
    salary_ranges: Mapped[dict] = mapped_column(JSONB, default=dict)

    last_updated_by: Mapped[Optional[str]] = mapped_column(String(100))
    last_updated_at: Mapped[Optional[datetime]] = mapped_column()
    data_source: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("idx_countries_currency", "currency"),
        Index("idx_countries_primary_visa", "primary_visa"),
    )

    def __repr__(self) -> str:
        return f"<Country({self.iso_code}: {self.name})>"
