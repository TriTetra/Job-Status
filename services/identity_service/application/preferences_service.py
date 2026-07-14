"""User preferences service."""

from typing import Dict

from core.db.connection import db
from core.db.repositories import UserSettingsRepository
from core.domain import UserPreferences


class PreferencesService:
    """Manages user preferences and scoring weights."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    def get_preferences(self) -> UserPreferences:
        """Return UserPreferences from DB (defaults if no row)."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)
            settings = repo.get_settings(self.user_id)
            if not settings or not settings.preferences:
                return UserPreferences()

            p = settings.preferences
            return UserPreferences(
                remote=p.get("remote", True),
                hybrid_acceptable=p.get("hybrid_acceptable", True),
                onsite_acceptable=p.get("onsite_acceptable", False),
                work_visa_required=p.get("work_visa_required", False),
                min_salary=p.get("min_salary"),
                max_salary=p.get("max_salary"),
                preferred_company_sizes=p.get("preferred_company_sizes", []),
                preferred_locations=p.get("preferred_locations", []),
            )

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist preferences back to DB."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)
            repo.upsert(
                user_id=self.user_id,
                preferences={
                    "remote": preferences.remote,
                    "hybrid_acceptable": preferences.hybrid_acceptable,
                    "onsite_acceptable": preferences.onsite_acceptable,
                    "work_visa_required": preferences.work_visa_required,
                    "min_salary": preferences.min_salary,
                    "max_salary": preferences.max_salary,
                    "preferred_company_sizes": preferences.preferred_company_sizes,
                    "preferred_locations": preferences.preferred_locations,
                },
            )

    def get_weights(self) -> Dict[str, float]:
        """Return scoring weights (with defaults)."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)
            return repo.get_weights(self.user_id)

    def save_weights(self, weights: Dict[str, float]) -> None:
        """Persist scoring weights."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)
            repo.set_weights(self.user_id, weights)
