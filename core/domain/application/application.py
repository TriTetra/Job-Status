"""Application domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ApplicationStatus(str, Enum):
    TO_APPLY = "to_apply"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    ONSITE = "onsite"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"


@dataclass
class Application:
    user_id: str
    url: str
    title: str
    company: str
    status: ApplicationStatus = ApplicationStatus.TO_APPLY

    applied_at: Optional[datetime] = None
    last_updated_at: datetime = field(default_factory=datetime.utcnow)

    resume_version: Optional[str] = None
    notes: str = ""
    salary_offered: Optional[int] = None
    response_days: Optional[int] = None

    interview_rounds: List[dict] = field(default_factory=list)

    def is_active(self) -> bool:
        return self.status in (
            ApplicationStatus.APPLIED,
            ApplicationStatus.PHONE_SCREEN,
            ApplicationStatus.TECHNICAL,
            ApplicationStatus.ONSITE,
        )

    def days_since_applied(self) -> Optional[int]:
        if not self.applied_at:
            return None
        return (datetime.utcnow() - self.applied_at).days
