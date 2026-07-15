"""Preferences API — career preferences CRUD.

Separate from onboarding router so preferences can be updated
after onboarding completes (career evolution).
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from core.db.repositories.career_preferences_repo import CareerPreferencesRepository

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


# ─── Response schemas ─────────────────────────────────────────────────────────

class SalaryOut(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = None
    period: str = "year"
    negotiable: bool = True


class PreferencesOut(BaseModel):
    goal_ids: list[str] = []
    preferred_role_ids: list[str] = []
    preferred_country_codes: list[str] = []
    work_arrangements: list[str] = []
    salary: Optional[SalaryOut] = None
    pref_metadata: dict = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ─── Request schemas ──────────────────────────────────────────────────────────

class PreferencesPatch(BaseModel):
    goal_ids: Optional[list[str]] = None
    preferred_role_ids: Optional[list[str]] = None
    preferred_country_codes: Optional[list[str]] = None
    work_arrangements: Optional[list[str]] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    salary_period: Optional[str] = Field(None, pattern="^(year|month)$")
    salary_negotiable: Optional[bool] = None
    pref_metadata: Optional[dict] = None


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_response(prefs) -> PreferencesOut:
    salary = None
    if prefs and (prefs.salary_min is not None or prefs.salary_max is not None):
        salary = SalaryOut(
            min=prefs.salary_min,
            max=prefs.salary_max,
            currency=prefs.salary_currency,
            period=prefs.salary_period or "year",
            negotiable=prefs.salary_negotiable if prefs.salary_negotiable is not None else True,
        )
    return PreferencesOut(
        goal_ids=prefs.goal_ids or [] if prefs else [],
        preferred_role_ids=prefs.preferred_role_ids or [] if prefs else [],
        preferred_country_codes=prefs.preferred_country_codes or [] if prefs else [],
        work_arrangements=prefs.work_arrangements or [] if prefs else [],
        salary=salary,
        pref_metadata=prefs.pref_metadata or {} if prefs else {},
        created_at=prefs.created_at.isoformat() if prefs and prefs.created_at else None,
        updated_at=prefs.updated_at.isoformat() if prefs and prefs.updated_at else None,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=PreferencesOut)
def get_preferences(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    repo = CareerPreferencesRepository(session)
    prefs = repo.get_by_user_id(user_id)
    return _to_response(prefs)


@router.patch("", response_model=PreferencesOut)
def patch_preferences(
    data: PreferencesPatch,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    repo = CareerPreferencesRepository(session)
    prefs = repo.get_by_user_id(user_id)
    if not prefs:
        prefs = repo.create(user_id=user_id)

    if data.goal_ids is not None:
        if len(data.goal_ids) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 goals allowed")
        prefs.goal_ids = data.goal_ids

    if data.preferred_role_ids is not None:
        prefs.preferred_role_ids = data.preferred_role_ids
    if data.preferred_country_codes is not None:
        prefs.preferred_country_codes = data.preferred_country_codes
    if data.work_arrangements is not None:
        prefs.work_arrangements = data.work_arrangements
    if data.salary_min is not None:
        prefs.salary_min = data.salary_min
    if data.salary_max is not None:
        prefs.salary_max = data.salary_max
    if data.salary_currency is not None:
        prefs.salary_currency = data.salary_currency
    if data.salary_period is not None:
        prefs.salary_period = data.salary_period
    if data.salary_negotiable is not None:
        prefs.salary_negotiable = data.salary_negotiable
    if data.pref_metadata is not None:
        prefs.pref_metadata = data.pref_metadata

    if prefs.salary_min is not None and prefs.salary_max is not None:
        if prefs.salary_min > prefs.salary_max:
            raise HTTPException(
                status_code=400,
                detail="salary_min cannot be greater than salary_max",
            )

    prefs.updated_at = datetime.utcnow()
    session.commit()
    return _to_response(prefs)
