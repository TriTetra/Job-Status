"""Application tracking model — full pipeline state machine."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careeros.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from careeros.applications.models.email import Email


class Application(Base, TimestampMixin):
    """
    One row per job URL. Status field drives the pipeline:

        to_apply → applied → phone_screen → technical
                                          → onsite → offer
                                                   → rejected | ghosted
    """

    __tablename__ = "applications"

    url: Mapped[str] = mapped_column(String(2048), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default", index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))

    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="to_apply",
    )

    resume_version: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    salary_offered: Mapped[int | None] = mapped_column(Integer)
    response_days: Mapped[int | None] = mapped_column(Integer)

    # [{"round": 1, "type": "phone_screen", "date": "2026-07-15", "notes": "..."}]
    interview_rounds: Mapped[list] = mapped_column(JSONB, default=list)

    emails: Mapped[list["Email"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Application url={self.url[:60]}... status={self.status}>"
