"""Roles API — search and retrieve canonical tech roles."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db_session
from core.domain.identity.role import Role


router = APIRouter(prefix="/api/roles", tags=["roles"])


# ─── Response Schemas ─────────────────────────────────────────

class RoleOut(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    aliases: list[str] = []
    metadata: dict = {}


class RoleSearchResult(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    aliases: list[str] = []
    score: int = 0


# ─── Endpoints ────────────────────────────────────────────────

@router.get("", response_model=List[RoleOut])
def list_all_roles(session: Session = Depends(get_db_session)):
    """Get all canonical roles ordered by category then title."""
    roles = session.query(Role).order_by(Role.category, Role.title).all()
    return [
        RoleOut(
            id=str(r.id),
            slug=r.slug,
            title=r.title,
            category=r.category,
            aliases=r.aliases or [],
            metadata=r.metadata_ or {},
        )
        for r in roles
    ]


@router.get("/search", response_model=List[RoleSearchResult])
def search_roles(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_db_session),
):
    """Fuzzy search roles by title, aliases, and category with relevance scoring."""
    q_lower = q.lower().strip()

    rows = (
        session.query(Role)
        .filter(
            text(
                "LOWER(title) LIKE :q"
                " OR LOWER(slug) LIKE :q"
                " OR LOWER(category) LIKE :q"
                " OR LOWER(aliases::text) LIKE :q"
            ).bindparams(q=f"%{q_lower}%")
        )
        .limit(limit * 3)
        .all()
    )

    results: list[RoleSearchResult] = []
    for r in rows:
        title_l = r.title.lower()
        slug_l = r.slug.lower()
        aliases_l = [a.lower() for a in (r.aliases or [])]
        score = 0

        # Title
        if title_l == q_lower:
            score += 1000
        elif title_l.startswith(q_lower):
            score += 500
        elif q_lower in title_l:
            score += 200

        # Slug
        if slug_l == q_lower:
            score += 800
        elif slug_l.startswith(q_lower):
            score += 400
        elif q_lower in slug_l:
            score += 150

        # Aliases
        if q_lower in aliases_l:
            score += 300
        elif any(q_lower in a for a in aliases_l):
            score += 100

        # Category
        if q_lower in r.category.lower():
            score += 50

        if score > 0:
            results.append(
                RoleSearchResult(
                    id=str(r.id),
                    slug=r.slug,
                    title=r.title,
                    category=r.category,
                    aliases=r.aliases or [],
                    score=score,
                )
            )

    results.sort(key=lambda x: (-x.score, x.title))
    return results[:limit]


@router.get("/categories", response_model=List[str])
def list_categories(session: Session = Depends(get_db_session)):
    """Get all unique role categories."""
    rows = session.execute(
        text("SELECT DISTINCT category FROM roles ORDER BY category")
    ).fetchall()
    return [row[0] for row in rows]


@router.get("/{slug}", response_model=RoleOut)
def get_role_by_slug(slug: str, session: Session = Depends(get_db_session)):
    """Get a single role by slug."""
    role = session.query(Role).filter(Role.slug == slug).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{slug}' not found")
    return RoleOut(
        id=str(role.id),
        slug=role.slug,
        title=role.title,
        category=role.category,
        aliases=role.aliases or [],
        metadata=role.metadata_ or {},
    )
