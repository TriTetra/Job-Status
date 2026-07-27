"""Goals catalog — role-aware, registry-driven (no hardcoded list)."""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from .evidence import _infer_category  # P0-c keyword inference, reused here

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


def _resolve_category(session: Session, user_id: str) -> tuple[Optional[str], Optional[str]]:
    """Return (category, role_title) for the user's current role (canonical or custom)."""
    row = session.execute(
        text("SELECT current_role_id, current_custom_role_id FROM users WHERE clerk_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        return None, None
    if row[0]:
        r = session.execute(
            text("SELECT title, category FROM roles WHERE id = :rid"),
            {"rid": str(row[0])},
        ).fetchone()
        return (r[1], r[0]) if r else (None, None)
    if row[1]:
        r = session.execute(
            text("SELECT title FROM custom_roles WHERE id = :cid"),
            {"cid": str(row[1])},
        ).fetchone()
        title = r[0] if r else None
        return _infer_category(title), title
    return None, None


@router.get("/catalog", response_model=GoalCatalogOut)
def get_goal_catalog(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Return visible goals filtered and sorted by the user's role category.

    - goals where category ∉ applicable are hidden (profession never sees them)
    - goals where category ∈ priority_for get suggested=True (pulsed dot in UI)
    """
    category, title = _resolve_category(session, user_id)

    rows = session.execute(
        text("SELECT id, label, theme, applicable, priority_for FROM goals ORDER BY sort_order")
    ).fetchall()

    goals: list[GoalOut] = []
    for gid, label, theme, applicable, priority_for in rows:
        applicable = applicable or []
        priority_for = priority_for or []
        if category and category not in applicable:
            continue  # this profession never sees this goal
        goals.append(GoalOut(
            id=gid, label=label, theme=theme,
            suggested=bool(category and category in priority_for),
        ))

    return GoalCatalogOut(goals=goals, role_title=title, role_category=category)
