"""What Aplio noticed in a person's mailbox about one of their applications.

Only the facts are kept: when, from which domain, the subject, what kind of answer it was
and a short quote that shows why. Never the message body. Forgetting the mailbox deletes
these rows with the connection (careeros/applications/mail/account.py).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin

KINDS = ("rejection", "interview", "offer", "info_request", "acknowledgment", "other")
# applied: the application's status was moved · pending: the person confirms · dismissed · noted: nothing to do
STATES = ("applied", "pending", "dismissed", "noted")


class MailSignal(Base, TimestampMixin):
    __tablename__ = "mail_signals"
    __table_args__ = (
        UniqueConstraint("user_id", "message_key", name="uq_mail_signals_user_message"),
        Index("idx_mail_signals_user_state", "user_id", "state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_key: Mapped[str] = mapped_column(String(64), nullable=False)      # sha256 of the Message-ID
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)    # the application it is about
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    from_domain: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    subject: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[str] = mapped_column(String(300), nullable=False, default="")   # a short quote, not the body
    state: Mapped[str] = mapped_column(String(12), nullable=False)
    status_before: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status_after: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
