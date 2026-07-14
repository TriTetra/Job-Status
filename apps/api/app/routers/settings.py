"""Settings router — scoring weights and user preferences."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from packages.db.repositories import UserSettingsRepository

router = APIRouter()


class WeightsResponse(BaseModel):
    user_id: str
    weights: Dict[str, float]


class WeightsUpdate(BaseModel):
    weights: Dict[str, float]


class SkillEntry(BaseModel):
    name: str
    level: str = "intermediate"
    ai_multiplier: float = 1.0
    evidence: List[str] = []


class SettingsResponse(BaseModel):
    user_id: str
    profile: Dict[str, Any]
    skills: Any
    preferences: Dict[str, Any]
    weights: Dict[str, float]


@router.get("/", response_model=SettingsResponse)
def get_settings(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Full user settings."""
    repo = UserSettingsRepository(session)
    row = repo.get_settings(user_id=user_id)
    if row:
        return SettingsResponse(
            user_id=user_id,
            profile=row.profile or {},
            skills=row.skills or [],
            preferences=row.preferences or {},
            weights=repo.get_weights(user_id=user_id),
        )
    return SettingsResponse(
        user_id=user_id,
        profile={},
        skills=[],
        preferences={},
        weights=repo.get_weights(user_id=user_id),
    )


@router.get("/weights", response_model=WeightsResponse)
def get_weights(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Scoring weights for the user (with defaults)."""
    repo = UserSettingsRepository(session)
    return WeightsResponse(user_id=user_id, weights=repo.get_weights(user_id=user_id))


@router.put("/weights", response_model=WeightsResponse)
def update_weights(
    data: WeightsUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Update scoring weights (partial — unspecified keys keep defaults)."""
    repo = UserSettingsRepository(session)
    repo.set_weights(user_id=user_id, weights=data.weights)
    return WeightsResponse(user_id=user_id, weights=repo.get_weights(user_id=user_id))


@router.put("/", response_model=SettingsResponse)
def upsert_settings(
    data: SettingsResponse,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Create or update full user settings."""
    repo = UserSettingsRepository(session)
    row = repo.upsert(
        user_id=user_id,
        profile=data.profile or None,
        skills=data.skills or None,
        preferences=data.preferences or None,
        weights=data.weights or None,
    )
    return SettingsResponse(
        user_id=user_id,
        profile=row.profile or {},
        skills=row.skills or [],
        preferences=row.preferences or {},
        weights=row.weights or {},
    )
