"""Skill model — canonical skills taxonomy."""

from typing import Optional
from sqlalchemy import String, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    aliases: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, nullable=True)
    related_skill_ids: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, nullable=True)
    skill_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_skills_category", "category"),
        Index("idx_skills_name_gin", "name", postgresql_ops={"name": "gin_trgm_ops"},
              postgresql_using="gin"),
    )
