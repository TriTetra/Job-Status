"""ConnectedAccount model — OAuth integrations (GitHub, LinkedIn, etc.)."""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class ConnectedAccount(Base, TimestampMixin):
    __tablename__ = "connected_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    provider_username: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    access_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    scopes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    account_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    __table_args__ = (
        Index("idx_connected_accounts_user_provider", "user_id", "provider", unique=True),
    )
