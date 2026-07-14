"""Repository layer — domain queries over SQLAlchemy models."""

from .base import BaseRepository
from .career_score_repo import CareerScoreRepository
from .application_repo import ApplicationRepository
from .scan_history_repo import ScanHistoryRepository
from .evidence_repo import EvidenceRepository
from .job_repo import JobRepository
from .user_settings_repo import UserSettingsRepository
from .company_repo import CompanyRepository, CompanyMemoryRepository
from .market_signal_repo import MarketSignalRepository
from .country_repo import CountryRepository
from .visa_repo import VisaRepository
from .salary_repo import SalaryRangeRepository

__all__ = [
    "BaseRepository",
    "CareerScoreRepository",
    "ApplicationRepository",
    "ScanHistoryRepository",
    "EvidenceRepository",
    "JobRepository",
    "UserSettingsRepository",
    "CompanyRepository",
    "CompanyMemoryRepository",
    "MarketSignalRepository",
    "CountryRepository",
    "VisaRepository",
    "SalaryRangeRepository",
]
