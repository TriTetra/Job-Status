"""Role model — canonical tech roles with ESCO/O*NET mapping."""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Integer, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from core.db.models.base import Base


class Role(Base):
    """Canonical tech role with aliases, metadata, and external mappings."""
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    aliases: Mapped[List[str]] = mapped_column(JSONB, default=list, server_default="[]")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    # External mappings (Phase 2'de doldurulacak)
    esco_id: Mapped[Optional[str]] = mapped_column(String(50))
    soc_code: Mapped[Optional[str]] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default="now()"
    )

    def __repr__(self) -> str:
        return f"<Role({self.slug}, {self.title})>"
