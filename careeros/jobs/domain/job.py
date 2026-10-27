"""Job domain entity."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Job:
    """Job posting."""

    id: str
    title: str
    company: str
    description: str
    url: str
    location: str = ""
    remote: bool = False
    hybrid: bool = False
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_years: float = 0.0
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    company_size: str = "unknown"
    industry: str = "unknown"
    funding_stage: str = "unknown"
    sponsors_visa: Optional[bool] = None  # None = the posting doesn't say
    posted_date: Optional[datetime] = None
    source: str = "unknown"
    fit_score: Optional[float] = None
    acceptance_probability: Optional[float] = None
    career_score: Optional[float] = None

    def days_since_posted(self) -> int:
        if not self.posted_date:
            return 0
        return (datetime.now() - self.posted_date).days

    def salary_range_str(self) -> str:
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} - ${self.salary_max:,}"
        elif self.salary_min:
            return f"${self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,}"
        return "Not specified"

    def all_skills(self) -> List[str]:
        return list(set(self.required_skills + self.preferred_skills))
