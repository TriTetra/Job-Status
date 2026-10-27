"""RoleAlias model — title evolution tracking."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RoleAlias(Base):
    """Tracks role title changes over time for audit and migration."""
    __tablename__ = "role_aliases"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)
    role_id: Mapped[str] = mapped_column(Uuid, ForeignKey("roles.id"), nullable=False)
    old_title: Mapped[str] = mapped_column(String(150), nullable=False)
    new_title: Mapped[str] = mapped_column(String(150), nullable=False)
    old_slug: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_slug: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default="now()"
    )
    changed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<RoleAlias(role={self.role_id}, {self.old_title} -> {self.new_title})>"
