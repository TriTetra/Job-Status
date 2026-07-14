"""User settings model — per-user profile, skills, preferences, and scoring weights."""

from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSettings(Base):
    """
    One row per user. Stores everything that used to live in config.yaml
    so the frontend can read and write it per user.

    JSONB columns let the schema evolve without migrations for every new field.
    """

    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Identity & experience
    profile: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="name, email, years_experience, current_title, target_roles, etc.",
    )

    # Skills list: [{name, level, ai_multiplier, evidence:[]}]
    skills: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="List of skill objects with level and ai_multiplier",
    )

    # Preferences: remote, hybrid, visa, salary_min, salary_max, company_sizes
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Scoring weights: {fit, acceptance, career_value, market_demand}
    # Defaults replicate the hardcoded 0.30/0.25/0.25/0.20 formula
    weights: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "fit": 0.30,
            "acceptance": 0.25,
            "career_value": 0.25,
            "market_demand": 0.20,
        },
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
