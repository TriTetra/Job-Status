"""Goals API — role-aware catalog for the onboarding goals step."""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.onboarding.goals_catalog import goal_catalog

from ..dependencies import get_db_session, get_user_id

router = APIRouter(prefix="/api/goals", tags=["goals"])


class GoalOut(BaseModel):
    id: str
    label: str
    theme: str
    suggested: bool


class GoalCatalogOut(BaseModel):
    goals: list[GoalOut]
    role_title: Optional[str] = None
    role_category: Optional[str] = None


@router.get("/catalog", response_model=GoalCatalogOut)
def get_goal_catalog(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Goals visible to the user's profession; those it prioritizes come back suggested=True."""
    return GoalCatalogOut(**goal_catalog(session, user_id))
