"""ResumeDocument model — uploaded CV/resume files per user."""

from typing import Optional
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ResumeDocument(Base, TimestampMixin):
    __tablename__ = "resume_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    parsed_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parse_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
