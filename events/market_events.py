"""Market intelligence events."""

from dataclasses import dataclass, field
from typing import List

from .event_types import Event


@dataclass
class SkillTrendDetected(Event):
    """Skill demand trend detected."""

    skill: str = ""
    direction: str = "up"  # up, down, stable
    magnitude: float = 0.0
    period_days: int = 7
    job_count_before: int = 0
    job_count_after: int = 0


@dataclass
class MarketSignalDetected(Event):
    """Generic market signal (funding, layoff, acquisition, etc.)."""

    signal_type: str = ""  # funding, layoff, acquisition, office_opening
    source: str = ""
    impact: str = "medium"  # low, medium, high
    companies_affected: List[str] = field(default_factory=list)
    skills_affected: List[str] = field(default_factory=list)
    news_url: str = ""
    summary: str = ""


@dataclass
class SalaryTrendUpdated(Event):
    """Salary trend updated for country/role combination."""

    country: str = ""
    role: str = ""
    change_percent: float = 0.0
    old_median: int = 0
    new_median: int = 0
    currency: str = "USD"
