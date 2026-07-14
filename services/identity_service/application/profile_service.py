"""User profile service."""

from typing import Optional

from core.db.connection import db
from core.db.repositories import UserSettingsRepository
from core.domain import UserPreferences, UserProfile


class ProfileService:
    """Manages user profiles — reads/writes UserSettings rows."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    def get_profile(self) -> Optional[UserProfile]:
        """Build a UserProfile from the DB row (returns None if no row exists)."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)
            settings = repo.get_settings(self.user_id)
            if not settings:
                return None

            p = settings.profile or {}
            prefs_data = settings.preferences or {}
            skills_data = settings.skills or []

            from core.domain.identity.skill import Skill, SkillLevel
            skills = [
                Skill(
                    name=s["name"],
                    level=SkillLevel(s.get("level", 2)),
                    ai_multiplier=s.get("ai_multiplier", 1.0),
                )
                for s in skills_data
                if isinstance(s, dict) and "name" in s
            ]

            preferences = UserPreferences(
                remote=prefs_data.get("remote", True),
                hybrid_acceptable=prefs_data.get("hybrid_acceptable", True),
                onsite_acceptable=prefs_data.get("onsite_acceptable", False),
                work_visa_required=prefs_data.get("work_visa_required", False),
                min_salary=prefs_data.get("min_salary"),
                max_salary=prefs_data.get("max_salary"),
                preferred_company_sizes=prefs_data.get("preferred_company_sizes", []),
                preferred_locations=prefs_data.get("preferred_locations", []),
            )

            return UserProfile(
                name=p.get("name", ""),
                email=p.get("email", ""),
                years_experience=p.get("years_experience", 0.0),
                skills=skills,
                preferences=preferences,
                target_roles=p.get("target_roles", []),
                target_domains=p.get("target_domains", []),
            )

    def save_profile(self, profile: UserProfile) -> None:
        """Persist a UserProfile back to the DB."""
        with db.session_scope() as session:
            repo = UserSettingsRepository(session)

            profile_data = {
                "name": profile.name,
                "email": profile.email,
                "years_experience": profile.years_experience,
                "target_roles": profile.target_roles,
                "target_domains": profile.target_domains,
            }
            skills_data = [
                {
                    "name": s.name,
                    "level": int(s.level),
                    "ai_multiplier": s.ai_multiplier,
                }
                for s in profile.skills
            ]
            prefs = profile.preferences
            prefs_data = {
                "remote": prefs.remote,
                "hybrid_acceptable": prefs.hybrid_acceptable,
                "onsite_acceptable": prefs.onsite_acceptable,
                "work_visa_required": prefs.work_visa_required,
                "min_salary": prefs.min_salary,
                "max_salary": prefs.max_salary,
                "preferred_company_sizes": prefs.preferred_company_sizes,
                "preferred_locations": prefs.preferred_locations,
            }

            repo.upsert(
                user_id=self.user_id,
                profile=profile_data,
                skills=skills_data,
                preferences=prefs_data,
            )
