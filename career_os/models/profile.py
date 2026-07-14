"""Backward compat shim — use packages.domain instead."""

from packages.domain.identity.profile import Experience, UserPreferences, UserProfile
from packages.domain.job.job import Job
from packages.domain.intelligence.match import MatchResult
from packages.domain.intelligence.scoring import OpportunityScore

__all__ = [
    "Experience", "UserPreferences", "UserProfile",
    "Job", "MatchResult", "OpportunityScore",
]
