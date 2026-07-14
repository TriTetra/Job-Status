"""Company domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .event_types import Event


@dataclass
class CompanyUpdated(Event):
    """Company profile updated with new information."""

    company_id: str = ""
    company_name: str = ""
    changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyHiringSpike(Event):
    """Company started hiring aggressively."""

    company_id: str = ""
    company_name: str = ""
    job_count: int = 0
    new_jobs_this_week: int = 0
    top_skills: List[str] = field(default_factory=list)


@dataclass
class CompanyLayoff(Event):
    """Company announced layoffs."""

    company_id: str = ""
    company_name: str = ""
    news_url: str = ""
    affected_roles: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high
