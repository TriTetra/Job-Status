"""User domain model — one row per Clerk identity."""

from enum import Enum
from typing import Optional

from sqlalchemy import String, ForeignKey, Float, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import Base, TimestampMixin


class OnboardingState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IDENTITY = "IDENTITY"
    GOALS = "GOALS"
    EVIDENCE = "EVIDENCE"
    CONNECTIONS = "CONNECTIONS"
    BUILDING = "BUILDING"
    READY = "READY"

    @staticmethod
    def next_state(current: str) -> Optional[str]:
        order = [s.value for s in OnboardingState]
        try:
            idx = order.index(current)
        except ValueError:
            return None
        return order[idx + 1] if idx + 1 < len(order) else None

    def next(self) -> Optional["OnboardingState"]:
        nxt = OnboardingState.next_state(self.value)
        return OnboardingState(nxt) if nxt else None

    @property
    def is_complete(self) -> bool:
        return self == OnboardingState.READY


class User(Base, TimestampMixin):
    __tablename__ = "users"

    clerk_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    onboarding_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OnboardingState.NOT_STARTED.value,
        server_default=OnboardingState.NOT_STARTED.value,
    )
    # Identity step: name, country, work authorization
    profile_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    # Goals step: optimizing_for, preferred_roles, countries, salary range
    goals: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # Career identity fields (UUID FK to roles/custom_roles)
    current_role_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("roles.id"), nullable=True)
    current_custom_role_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("custom_roles.id"), nullable=True)
    years_in_role: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    career_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    career_level_origin: Mapped[Optional[str]] = mapped_column(String(30), server_default="user")

    @property
    def display_name(self) -> str:
        if self.first_name:
            return f"{self.first_name} {self.last_name or ''}".strip()
        return self.email.split("@")[0]

    @property
    def onboarding(self) -> OnboardingState:
        return OnboardingState(self.onboarding_state)

    def advance_onboarding(self) -> "User":
        nxt = self.onboarding.next()
        if nxt:
            self.onboarding_state = nxt.value
        return self
