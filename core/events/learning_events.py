"""Learning engine events."""

from dataclasses import dataclass, field
from typing import List

from .event_types import Event


@dataclass
class SkillLearned(Event):
    """User marked a skill as learned."""

    user_id: str = ""
    skill: str = ""
    hours_spent: float = 0.0
    evidence: List[str] = field(default_factory=list)
    new_level: str = ""  # AI_ASSISTED, WORKING, INDEPENDENT, ADVANCED, EXPERT


@dataclass
class RoadmapGenerated(Event):
    """Learning roadmap generated for user."""

    user_id: str = ""
    skills: List[str] = field(default_factory=list)
    timeline_weeks: int = 0
    total_hours: int = 0
    expected_fit_improvement: float = 0.0


@dataclass
class ROICalculated(Event):
    """ROI calculated for a skill."""

    skill: str = ""
    unlocked_jobs: int = 0
    learning_hours: int = 0
    roi_score: float = 0.0  # unlocked_jobs / learning_hours
    salary_impact: int = 0
