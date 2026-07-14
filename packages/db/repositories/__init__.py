"""Repository layer — domain queries over SQLAlchemy models."""

from .base import BaseRepository
from .career_score_repo import CareerScoreRepository
from .application_repo import ApplicationRepository
from .scan_history_repo import ScanHistoryRepository
from .evidence_repo import EvidenceRepository
from .job_repo import JobRepository
from .user_settings_repo import UserSettingsRepository

__all__ = [
    "BaseRepository",
    "CareerScoreRepository",
    "ApplicationRepository",
    "ScanHistoryRepository",
    "EvidenceRepository",
    "JobRepository",
    "UserSettingsRepository",
]
