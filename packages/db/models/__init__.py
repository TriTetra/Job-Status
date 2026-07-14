"""Database models package."""

from .base import Base, TimestampMixin
from .career_score import CareerScore
from .application import Application
from .email import Email
from .scan_history import ScanHistory
from .evidence import Evidence
from .job import Job
from .user_settings import UserSettings
from .user_custom_skills import UserCustomSkill
from .company import Company
from .company_memory import CompanyMemory
from .market_signal import MarketSignal
from .timeline import TimelineSnapshot, TimelineChange
from .country import Country
from .visa import Visa
from .salary_range import SalaryRange

__all__ = [
    "Base",
    "TimestampMixin",
    "CareerScore",
    "Application",
    "Email",
    "ScanHistory",
    "Evidence",
    "Job",
    "UserSettings",
    "UserCustomSkill",
    "Company",
    "CompanyMemory",
    "MarketSignal",
    "TimelineSnapshot",
    "TimelineChange",
    "Country",
    "Visa",
    "SalaryRange",
]
