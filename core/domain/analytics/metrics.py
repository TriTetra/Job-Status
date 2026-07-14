"""Analytics metrics."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AnalyticsMetrics:
    user_id: str
    period_days: int = 30

    applications_submitted: int = 0
    interviews_scheduled: int = 0
    offers_received: int = 0
    rejections: int = 0

    avg_response_days: float = 0.0
    ghosted_count: int = 0

    skills_learned: List[str] = field(default_factory=list)
    evidence_added: int = 0

    resumes_generated: int = 0
    resume_versions: Dict[str, int] = field(default_factory=dict)

    top_companies: List[str] = field(default_factory=list)
    best_template: Optional[str] = None

    def get_interview_rate(self) -> float:
        if self.applications_submitted == 0:
            return 0.0
        return self.interviews_scheduled / self.applications_submitted

    def get_offer_rate(self) -> float:
        if self.interviews_scheduled == 0:
            return 0.0
        return self.offers_received / self.interviews_scheduled
