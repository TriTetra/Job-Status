"""Per-user application history with each company."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class CompanyMemory(Base, TimestampMixin):
    __tablename__ = "company_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default", index=True)
    company_name: Mapped[str] = mapped_column(
        String(200),
        ForeignKey("companies.name", ondelete="CASCADE"),
        nullable=False,
    )
    fact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    fact_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(default=1.0)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_company_memory_user_company", "user_id", "company_name"),
        Index("idx_company_memory_fact_type", "fact_type"),
        Index("idx_company_memory_fact_data", "fact_data", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<CompanyMemory(user={self.user_id}, company={self.company_name}, type={self.fact_type})>"
