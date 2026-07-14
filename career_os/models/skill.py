"""Backward compat shim — use packages.domain.identity.skill instead."""

from packages.domain.identity.skill import (
    Skill, SkillLevel, SKILL_CATEGORIES, categorize_skill,
)

__all__ = ["Skill", "SkillLevel", "SKILL_CATEGORIES", "categorize_skill"]
