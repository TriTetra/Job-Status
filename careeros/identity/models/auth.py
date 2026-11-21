"""Password credentials, server-side sessions and invite links (own auth — invite-only)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class AuthCredential(Base):
    """One password per user (argon2id hash)."""

    __tablename__ = "auth_credentials"

    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AuthSession(Base):
    """A signed-in browser. The cookie holds a random token; only its sha256 is stored."""

    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_auth_sessions_user", "user_id"),
        Index("idx_auth_sessions_expires", "expires_at"),
    )


class AuthInvite(Base):
    """A single-use sign-up link an admin sends to a friend. Only the token's sha256 is stored."""

    __tablename__ = "auth_invites"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)          # shown to admins, used to revoke
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)  # if set, only this address can use it
    created_by: Mapped[Optional[str]] = mapped_column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by: Mapped[Optional[str]] = mapped_column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
