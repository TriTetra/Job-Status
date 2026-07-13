"""Repository layer — domain queries over SQLAlchemy models."""

from .base import BaseRepository
from .career_score_repo import CareerScoreRepository
from .application_repo import ApplicationRepository
from .scan_history_repo import ScanHistoryRepository

__all__ = [
    "BaseRepository",
    "CareerScoreRepository",
    "ApplicationRepository",
    "ScanHistoryRepository",
]
