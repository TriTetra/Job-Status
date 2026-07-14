"""Backward compat shim — use packages.domain instead."""

from packages.domain import (
    Skill, SkillLevel, SKILL_CATEGORIES, categorize_skill,
    Experience, UserPreferences, UserProfile,
    Job, MatchResult, OpportunityScore,
)

__all__ = [
    "Skill", "SkillLevel", "SKILL_CATEGORIES", "categorize_skill",
    "Experience", "UserPreferences", "UserProfile",
    "Job", "MatchResult", "OpportunityScore",
]
