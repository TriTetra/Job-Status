"""Repository for user_settings and user_custom_skills tables."""

from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from careeros.identity.models.user_settings import UserSettings
from careeros.identity.models.user_custom_skills import UserCustomSkill
from careeros.db.repository import BaseRepository

_DEFAULT_WEIGHTS = {
    "fit": 0.30,
    "acceptance": 0.25,
    "career_value": 0.25,
    "market_demand": 0.20,
}


class UserSettingsRepository(BaseRepository[UserSettings]):
    model = UserSettings

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_settings(self, user_id: str) -> Optional[UserSettings]:
        return self.get(user_id=user_id)

    def get_weights(self, user_id: str) -> Dict[str, float]:
        """Return scoring weights for user, falling back to defaults."""
        row = self.get(user_id=user_id)
        if row and row.weights:
            return {**_DEFAULT_WEIGHTS, **row.weights}
        return _DEFAULT_WEIGHTS.copy()

    def get_skills(self, user_id: str) -> List[dict]:
        """Return skill list: [{name, level, ai_multiplier, evidence}]"""
        row = self.get(user_id=user_id)
        if row and row.skills:
            return row.skills if isinstance(row.skills, list) else []
        return []

    def get_profile(self, user_id: str) -> dict:
        row = self.get(user_id=user_id)
        return (row.profile or {}) if row else {}

    def get_preferences(self, user_id: str) -> dict:
        row = self.get(user_id=user_id)
        return (row.preferences or {}) if row else {}

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(
        self,
        user_id: str,
        *,
        profile: Optional[dict] = None,
        skills: Optional[list] = None,
        preferences: Optional[dict] = None,
        weights: Optional[dict] = None,
    ) -> UserSettings:
        """Create or update user settings. Only supplied fields are changed."""
        existing = self.get(user_id=user_id)
        if existing is None:
            existing = self.model(
                user_id=user_id,
                profile=profile or {},
                skills=skills or [],
                preferences=preferences or {},
                weights=weights or _DEFAULT_WEIGHTS.copy(),
            )
            self.session.add(existing)
        else:
            if profile is not None:
                existing.profile = profile
            if skills is not None:
                existing.skills = skills
            if preferences is not None:
                existing.preferences = preferences
            if weights is not None:
                existing.weights = weights
        self.session.flush()
        return existing

    def set_weights(self, user_id: str, weights: Dict[str, float]) -> None:
        """Partial update — only scoring weights."""
        existing = self.get(user_id=user_id)
        if existing:
            existing.weights = {**_DEFAULT_WEIGHTS, **weights}
        else:
            self.session.add(
                self.model(
                    user_id=user_id,
                    profile={},
                    skills=[],
                    preferences={},
                    weights={**_DEFAULT_WEIGHTS, **weights},
                )
            )
        self.session.flush()

    # ------------------------------------------------------------------
    # Custom skills
    # ------------------------------------------------------------------

    def add_custom_skill(
        self, user_id: str, skill_name: str, category: Optional[str] = None
    ) -> UserCustomSkill:
        stmt = (
            insert(UserCustomSkill)
            .values(user_id=user_id, skill_name=skill_name, category=category)
            .on_conflict_do_update(
                constraint="uq_user_custom_skills",
                set_={"category": category},
            )
            .returning(UserCustomSkill)
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.scalar_one()

    def get_custom_skills(self, user_id: str) -> List[str]:
        """Return list of custom skill names for this user."""
        rows = self.session.execute(
            sa.select(UserCustomSkill).where(
                UserCustomSkill.user_id == user_id
            )
        ).scalars().all()
        return [r.skill_name for r in rows]

    def remove_custom_skill(self, user_id: str, skill_name: str) -> None:
        row = self.session.execute(
            sa.select(UserCustomSkill).where(
                UserCustomSkill.user_id == user_id,
                UserCustomSkill.skill_name == skill_name,
            )
        ).scalar_one_or_none()
        if row:
            self.session.delete(row)
            self.session.flush()
