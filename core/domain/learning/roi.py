"""ROI calculation for skill learning."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillROI:
    skill_name: str

    learning_hours: int
    learning_cost_usd: Optional[int] = None

    unlocked_jobs: int = 0
    salary_increase_pct: float = 0.0
    interview_rate_increase_pct: float = 0.0

    roi_score: float = 0.0

    def calculate_roi(self) -> float:
        if self.learning_hours == 0:
            return 0.0
        self.roi_score = self.unlocked_jobs / self.learning_hours
        return self.roi_score

    def is_worth_learning(self, threshold: float = 0.5) -> bool:
        return self.calculate_roi() >= threshold

    def get_payback_period_weeks(self, hours_per_week: int = 10) -> int:
        if hours_per_week == 0:
            return 0
        return (self.learning_hours + hours_per_week - 1) // hours_per_week
