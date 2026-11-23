"""A user's Telegram chat and what has been sent to it."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base

DEFAULT_PREFS = {"matches": True, "reminders": True}


class TelegramLink(Base):
    __tablename__ = "telegram_links"
    __table_args__ = (Index("idx_telegram_links_token", "link_token_hash"),)

    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    linked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    prefs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: dict(DEFAULT_PREFS))
    # Keys already notified ("<job url>" for matches, "remind:<url>" for reminders); newest last
    sent: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # One-time connect link (only its hash is stored)
    link_token_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    link_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
