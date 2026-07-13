"""Email model — cold email + follow-up tracking."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Email(Base, TimestampMixin):
    """
    One row per email (initial + follow-ups).
    sent_at=NULL means generated but not yet sent.
    """

    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(
        String(2048),
        ForeignKey("applications.url", ondelete="CASCADE"),
        nullable=False,
    )

    # cold_email | follow_up_1 | follow_up_2 | thank_you
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 0 = initial, 1 = follow-up-1, 2 = follow-up-2
    sequence_num: Mapped[int] = mapped_column(Integer, default=0)

    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped["Application"] = relationship(back_populates="emails")

    def __repr__(self) -> str:
        return (
            f"<Email id={self.id} type={self.template_type} "
            f"sent={self.sent_at is not None}>"
        )
