"""Opportunity scoring domain entity."""

from dataclasses import dataclass

from core.domain.job.job import Job


@dataclass
class OpportunityScore:
    """Comprehensive opportunity evaluation."""

    job: Job
    fit_score: float
    acceptance_probability: float
    career_value: float
    market_demand: float
    career_score: float
    expected_value: float
    recommendation: str = ""

    def should_apply(self, threshold: float = 60.0) -> bool:
        return self.career_score >= threshold

    def priority_tier(self) -> str:
        if self.career_score >= 80:
            return "HIGH"
        elif self.career_score >= 60:
            return "MEDIUM"
        return "LOW"
