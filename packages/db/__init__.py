"""Database package — models, connection pool, repositories, migrations."""

from .connection import db, get_session, session_scope
from .models import Base, CareerScore, Application, Email, ScanHistory
from .repositories import (
    CareerScoreRepository,
    ApplicationRepository,
    ScanHistoryRepository,
)

__all__ = [
    "db",
    "get_session",
    "session_scope",
    "Base",
    "CareerScore",
    "Application",
    "Email",
    "ScanHistory",
    "CareerScoreRepository",
    "ApplicationRepository",
    "ScanHistoryRepository",
]
