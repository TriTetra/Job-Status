"""A prepared application for one job: the form's questions with suggested answers, the CV to
send and a short note. Aplio prepares it; the person reviews it and submits it themselves."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class ApplyKit(Base):
    __tablename__ = "apply_kits"

    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), primary_key=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # the posting version it was made for
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
