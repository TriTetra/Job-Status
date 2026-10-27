"""Repository layer — domain queries over SQLAlchemy models."""

from .base import BaseRepository
from .career_score_repo import CareerScoreRepository
from .application_repo import ApplicationRepository
from .scan_history_repo import ScanHistoryRepository
from .job_repo import JobRepository
from .user_settings_repo import UserSettingsRepository
from .company_repo import CompanyRepository, CompanyMemoryRepository
from .market_signal_repo import MarketSignalRepository
from .country_repo import CountryRepository
from .visa_repo import VisaRepository
from .salary_repo import SalaryRangeRepository
from .user_repo import UserRepository
from .role_repo import RoleRepository
from .career_preferences_repo import CareerPreferencesRepository

__all__ = [
    "BaseRepository",
    "CareerScoreRepository",
    "ApplicationRepository",
    "ScanHistoryRepository",
    "JobRepository",
    "UserSettingsRepository",
    "CompanyRepository",
    "CompanyMemoryRepository",
    "MarketSignalRepository",
    "CountryRepository",
    "VisaRepository",
    "SalaryRangeRepository",
    "UserRepository",
    "RoleRepository",
    "CareerPreferencesRepository",
]
