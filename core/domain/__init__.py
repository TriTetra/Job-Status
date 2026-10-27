"""CareerOS Domain Entities — pure business objects, no external dependencies."""

from .identity.onboarding import OnboardingState
from .identity.skill import Skill, SkillLevel, SKILL_CATEGORIES, categorize_skill
from .identity.profile import UserProfile, UserPreferences, Experience
from .job.job import Job
from .intelligence.match import MatchResult
from .intelligence.scoring import OpportunityScore

__all__ = [
    # Identity
    "OnboardingState",
    "Skill", "SkillLevel", "SKILL_CATEGORIES", "categorize_skill",
    "UserProfile", "UserPreferences", "Experience",
    # Job
    "Job",
    # Intelligence
    "MatchResult", "OpportunityScore",
]
