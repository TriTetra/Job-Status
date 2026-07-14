"""Application funnel analytics."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class FunnelStage:
    name: str
    count: int
    conversion_rate: float = 0.0


@dataclass
class ApplicationFunnel:
    user_id: str
    period_start: datetime
    period_end: datetime

    stages: List[FunnelStage] = field(default_factory=list)

    total_applications: int = 0
    total_interviews: int = 0
    total_offers: int = 0

    def calculate_conversion_rates(self) -> None:
        for i in range(1, len(self.stages)):
            prev = self.stages[i - 1].count
            if prev > 0:
                self.stages[i].conversion_rate = self.stages[i].count / prev

    def get_overall_conversion(self) -> float:
        if self.total_applications == 0:
            return 0.0
        return self.total_offers / self.total_applications
