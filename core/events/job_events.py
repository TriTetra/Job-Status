"""Job domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .event_types import Event


@dataclass
class JobDiscovered(Event):
    """New job discovered by scanner."""

    job_id: str = ""
    url: str = ""
    title: str = ""
    company: str = ""
    discovered_at: str = ""

    def __post_init__(self) -> None:
        if not self.job_id and self.url:
            self.job_id = self.url


@dataclass
class JobScored(Event):
    """Job scored by intelligence engine."""

    job_id: str = ""
    url: str = ""
    title: str = ""
    company: str = ""

    career_score: float = 0.0
    fit_score: float = 0.0
    acceptance_probability: float = 0.0
    career_value: float = 0.0
    market_demand: float = 0.0
    expected_value: float = 0.0

    recommendation: str = ""  # APPLY, CONSIDER, SKIP
    explanation: Dict[str, Any] = field(default_factory=dict)
    skill_gaps: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.job_id and self.url:
            self.job_id = self.url


@dataclass
class JobExpired(Event):
    """Job posting expired or removed."""

    job_id: str = ""
    url: str = ""
    reason: str = "expired"  # expired, removed, closed

    def __post_init__(self) -> None:
        if not self.job_id and self.url:
            self.job_id = self.url


@dataclass
class JobMatched(Event):
    """Job matched to user profile (high-confidence match)."""

    job_id: str = ""
    url: str = ""
    user_id: str = ""
    match_score: float = 0.0
    top_matched_skills: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.job_id and self.url:
            self.job_id = self.url
