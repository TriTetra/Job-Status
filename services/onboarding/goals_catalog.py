"""Goals catalog for the goals step — registry-driven (`goals` table), filtered by profession."""

from typing import Iterable, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from services.identity_service.application.current_role import get_current_role


def visible_goals(rows: Iterable[tuple], category: Optional[str]) -> list[dict]:
    """(id, label, theme, applicable, priority_for) rows → goals this profession may see.

    A goal is hidden when the user has a category that is not in `applicable`;
    it is suggested when the category is in `priority_for`.
    """
    goals = []
    for gid, label, theme, applicable, priority_for in rows:
        if category and category not in (applicable or []):
            continue
        goals.append({
            "id": gid,
            "label": label,
            "theme": theme,
            "suggested": bool(category and category in (priority_for or [])),
        })
    return goals


def goal_catalog(session: Session, user_id: str) -> dict:
    role = get_current_role(session, user_id)
    category = role.category if role else None
    rows = session.execute(
        sa.text("SELECT id, label, theme, applicable, priority_for FROM goals ORDER BY sort_order")
    ).fetchall()
    return {
        "goals": visible_goals(rows, category),
        "role_title": role.title if role else None,
        "role_category": category,
    }
