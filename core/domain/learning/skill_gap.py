"""Skill gap and learning roadmap entities."""

from dataclasses import dataclass, field
from typing import List

from core.domain.identity.skill import SkillLevel


@dataclass
class SkillGap:
    skill_name: str
    current_level: SkillLevel
    required_level: SkillLevel

    estimated_hours: int = 0
    transfer_discount: float = 1.0
    priority: float = 0.0

    def effective_hours(self) -> int:
        return int(self.estimated_hours * self.transfer_discount)

    def is_bridgeable(self, max_hours: int = 100) -> bool:
        return self.effective_hours() <= max_hours


@dataclass
class LearningTask:
    skill_name: str
    description: str
    estimated_hours: int
    resources: List[str] = field(default_factory=list)
    order: int = 0


@dataclass
class LearningRoadmap:
    user_id: str
    target_role: str
    tasks: List[LearningTask] = field(default_factory=list)

    total_hours: int = 0
    timeline_weeks: int = 0
    expected_fit_improvement: float = 0.0

    def get_weekly_plan(self, hours_per_week: int = 10) -> List[List[LearningTask]]:
        weeks: List[List[LearningTask]] = []
        current_week: List[LearningTask] = []
        current_hours = 0

        for task in sorted(self.tasks, key=lambda t: t.order):
            if current_hours + task.estimated_hours > hours_per_week:
                weeks.append(current_week)
                current_week = [task]
                current_hours = task.estimated_hours
            else:
                current_week.append(task)
                current_hours += task.estimated_hours

        if current_week:
            weeks.append(current_week)

        return weeks
