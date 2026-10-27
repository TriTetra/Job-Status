"""CustomRole model — user-defined roles with AI mapping to canonical roles."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Float, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from careeros.db.base import Base


class CustomRole(Base):
    """User-defined role with optional AI mapping to a canonical role."""
    __tablename__ = "custom_roles"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.clerk_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    mapped_role_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("roles.id"), nullable=True)
    mapping_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mapping_source: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    mapping_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    mapped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default="now()"
    )

    def __repr__(self) -> str:
        return f"<CustomRole(user={self.user_id}, title={self.title}, mapped={self.mapped_role_id})>"
