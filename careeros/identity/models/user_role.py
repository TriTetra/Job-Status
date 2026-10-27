"""UserRole model — career role history with XOR constraint."""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class UserRole(Base):
    """User's role history (current + past roles).
    
    XOR constraint: exactly one of role_id or custom_role_id must be set.
    """
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id"), nullable=False)
    role_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("roles.id"), nullable=True)
    custom_role_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("custom_roles.id"), nullable=True)
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    ended_at: Mapped[Optional[date]] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # 'canonical' | 'custom'

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default="now()"
    )

    def __repr__(self) -> str:
        return f"<UserRole(user={self.user_id}, role={self.role_id}, custom={self.custom_role_id}, current={self.is_current})>"
