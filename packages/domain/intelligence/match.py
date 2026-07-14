"""Match result domain entity."""

from dataclasses import dataclass, field
from typing import Dict, List

from packages.domain.job.job import Job


@dataclass
class MatchResult:
    """Result of matching a user profile to a job."""

    job: Job
    overall_score: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    skill_gaps: List[str] = field(default_factory=list)
    confidence: float = 0.0
    explanation: str = ""

    def summary(self) -> str:
        lines = [
            f"Match Score: {self.overall_score:.1f}/100",
            f"Confidence: {self.confidence:.0%}",
            "",
            "Breakdown:",
        ]
        for dimension, score in self.breakdown.items():
            lines.append(f"  {dimension}: {score:.1f}")
        if self.skill_gaps:
            lines.append("")
            lines.append(f"Missing {len(self.skill_gaps)} skills: {', '.join(self.skill_gaps[:5])}")
        return "\n".join(lines)
