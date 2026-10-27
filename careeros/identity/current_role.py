"""The user's current role and the profession category it implies.

Used to tailor onboarding: which goals to show and which evidence sources to
recommend. Canonical roles carry a category (and suggested sources) in the
`roles` table; for custom free-text roles the category is inferred from the title.
"""

from dataclasses import dataclass, field
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

# Custom-role title keywords → profession category (first match wins)
_CATEGORY_KEYWORDS: list[tuple[list[str], str]] = [
    (["doctor", "physician", "surgeon", "nurse", "medic", "clinical", "cardio",
      "oncolo", "radiolo", "dermato", "pediatr", "psychiat", "dentist", "dental",
      "pharmacist", "veterinar", "therapist", "clinician"], "medical"),
    (["professor", "researcher", "scientist", "postdoc", "phd", "academic",
      "lecturer", "scholar", "fellow"], "academic"),
    (["architect", "urban", "landscape architect", "interior designer", "planner"], "architecture"),
    (["artist", "illustrator", "photographer", "animator", "painter", "sculptor",
      "graphic designer", "art director", "creative director"], "visual_art"),
    (["writer", "author", "journalist", "editor", "copywriter", "content",
      "poet", "screenwriter", "blogger"], "writing"),
    (["teacher", "educator", "instructor", "tutor", "coach", "trainer",
      "principal"], "education"),
    (["lawyer", "attorney", "legal", "counsel", "paralegal", "solicitor",
      "barrister", "jurist"], "legal"),
]


def infer_category(title: Optional[str]) -> Optional[str]:
    """Map a free-text role title to a profession category, or None."""
    if not title:
        return None
    t = title.lower()
    for keywords, category in _CATEGORY_KEYWORDS:
        if any(k in t for k in keywords):
            return category
    return None


@dataclass(frozen=True)
class CurrentRole:
    title: Optional[str]
    category: Optional[str]
    is_custom: bool
    # Seeded on canonical roles only; custom roles fall back to their category
    suggested_source_ids: list[str] = field(default_factory=list)


def get_current_role(session: Session, user_id: str) -> Optional[CurrentRole]:
    """The user's current canonical or custom role, or None if not set."""
    row = session.execute(
        sa.text("SELECT current_role_id, current_custom_role_id FROM users WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        return None
    role_id, custom_role_id = row

    if role_id:
        r = session.execute(
            sa.text("SELECT title, category, metadata->'suggested_source_ids' FROM roles WHERE id = :rid"),
            {"rid": str(role_id)},
        ).fetchone()
        if not r:
            return None
        return CurrentRole(title=r[0], category=r[1], is_custom=False, suggested_source_ids=list(r[2] or []))

    if custom_role_id:
        r = session.execute(
            sa.text("SELECT title FROM custom_roles WHERE id = :cid"), {"cid": str(custom_role_id)}
        ).fetchone()
        title = r[0] if r else None
        return CurrentRole(title=title, category=infer_category(title), is_custom=True)

    return None
