"""SalaryRange entity — per role / region / level, seeded from YAML, editable via UI."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class SalaryRange(Base, TimestampMixin):
    __tablename__ = "salary_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    role_family: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    level: Mapped[str] = mapped_column(String(30), nullable=False)

    min_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    max_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    median_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    data_year: Mapped[int] = mapped_column(Integer, default=2026)
    source: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(String(1000))
    top_companies: Mapped[dict] = mapped_column(JSONB, default=dict)

    last_updated_by: Mapped[Optional[str]] = mapped_column(String(100))
    last_updated_at: Mapped[Optional[datetime]] = mapped_column()

    __table_args__ = (
        Index("idx_salary_role", "role_family"),
        Index("idx_salary_country", "country"),
        Index("idx_salary_level", "level"),
        Index("idx_salary_role_country", "role_family", "country"),
        Index("idx_salary_role_level", "role_family", "level"),
    )

    def __repr__(self) -> str:
        return f"<SalaryRange({self.role_family} {self.level}: {self.min_salary}-{self.max_salary} {self.currency})>"
