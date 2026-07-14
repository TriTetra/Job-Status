"""Application domain events."""

from dataclasses import dataclass, field
from typing import List, Optional

from .event_types import Event


@dataclass
class ApplicationSubmitted(Event):
    """User submitted an application."""

    job_id: str = ""
    url: str = ""
    user_id: str = ""
    company: str = ""
    title: str = ""
    resume_version: str = ""
    applied_at: str = ""  # ISO timestamp


@dataclass
class ApplicationRejected(Event):
    """Application rejected by company."""

    job_id: str = ""
    url: str = ""
    user_id: str = ""
    company: str = ""
    stage: str = ""  # phone_screen, technical, onsite
    reason: Optional[str] = None
    feedback: Optional[str] = None


@dataclass
class ApplicationInterview(Event):
    """User got an interview invitation."""

    job_id: str = ""
    url: str = ""
    user_id: str = ""
    company: str = ""
    round_name: str = ""  # phone_screen, technical, onsite, final
    scheduled_at: str = ""  # ISO timestamp
    interviewers: List[str] = field(default_factory=list)


@dataclass
class ApplicationOffer(Event):
    """User received an offer."""

    job_id: str = ""
    url: str = ""
    user_id: str = ""
    company: str = ""
    salary: Optional[int] = None
    currency: str = "USD"
    equity_percent: Optional[float] = None
    remote: bool = False
    deadline: Optional[str] = None  # ISO timestamp
