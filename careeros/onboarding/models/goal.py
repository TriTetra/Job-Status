"""Goal registry — role-aware motivation catalog (replaces the hardcoded GOALS const)."""
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from careeros.db.base import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    theme: Mapped[str] = mapped_column(String(30), nullable=False)
    applicable: Mapped[list] = mapped_column(JSONB, nullable=False)          # role categories (visibility)
    priority_for: Mapped[list] = mapped_column(JSONB, server_default="[]")   # categories that get the "for you" dot
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
