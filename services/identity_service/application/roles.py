"""Canonical role catalog: list, relevance search, categories, lookup by slug."""

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from core.db.models.role import Role

# Relevance weights: exact > prefix > substring; title beats slug beats aliases beats category
_TITLE = (1000, 500, 200)
_SLUG = (800, 400, 150)
_ALIAS_EXACT, _ALIAS_PARTIAL = 300, 100
_CATEGORY = 50


def _match(value: str, q: str, weights: tuple[int, int, int]) -> int:
    exact, prefix, contains = weights
    if value == q:
        return exact
    if value.startswith(q):
        return prefix
    return contains if q in value else 0


def relevance(role, query: str) -> int:
    """0 = no match. Pure: works on any object with title/slug/aliases/category."""
    q = query.lower().strip()
    aliases = [a.lower() for a in (role.aliases or [])]
    score = _match(role.title.lower(), q, _TITLE) + _match(role.slug.lower(), q, _SLUG)
    if q in aliases:
        score += _ALIAS_EXACT
    elif any(q in a for a in aliases):
        score += _ALIAS_PARTIAL
    if q in role.category.lower():
        score += _CATEGORY
    return score


def list_roles(session: Session) -> list[Role]:
    return session.query(Role).order_by(Role.category, Role.title).all()


def search_roles(session: Session, query: str, limit: int = 10) -> list[tuple[Role, int]]:
    """(role, score) best first. Candidates come from a LIKE prefilter, ranking is in Python."""
    pattern = f"%{query.lower().strip()}%"
    candidates = (
        session.query(Role)
        .filter(
            sa.text(
                "LOWER(title) LIKE :q OR LOWER(slug) LIKE :q"
                " OR LOWER(category) LIKE :q OR LOWER(aliases::text) LIKE :q"
            ).bindparams(q=pattern)
        )
        .limit(limit * 3)
        .all()
    )
    scored = [(r, relevance(r, query)) for r in candidates]
    scored = [(r, s) for r, s in scored if s > 0]
    scored.sort(key=lambda rs: (-rs[1], rs[0].title))
    return scored[:limit]


def list_categories(session: Session) -> list[str]:
    return [row[0] for row in session.execute(sa.text("SELECT DISTINCT category FROM roles ORDER BY category"))]


def get_role(session: Session, slug: str) -> Optional[Role]:
    return session.query(Role).filter(Role.slug == slug).first()
