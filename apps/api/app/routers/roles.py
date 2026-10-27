"""Roles API — search and retrieve canonical roles."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from careeros.identity import roles

from ..dependencies import get_db_session

router = APIRouter(prefix="/api/roles", tags=["roles"])


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


def _out(r) -> RoleOut:
    return RoleOut(id=str(r.id), slug=r.slug, title=r.title, category=r.category,
                   aliases=r.aliases or [], metadata=r.metadata_ or {})


@router.get("", response_model=List[RoleOut])
def list_all_roles(session: Session = Depends(get_db_session)):
    """All canonical roles ordered by category then title."""
    return [_out(r) for r in roles.list_roles(session)]


@router.get("/search", response_model=List[RoleSearchResult])
def search_roles(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_db_session),
):
    """Roles matching title, slug, aliases or category, most relevant first."""
    return [
        RoleSearchResult(id=str(r.id), slug=r.slug, title=r.title, category=r.category,
                         aliases=r.aliases or [], score=score)
        for r, score in roles.search_roles(session, q, limit)
    ]


@router.get("/categories", response_model=List[str])
def list_categories(session: Session = Depends(get_db_session)):
    """All unique role categories."""
    return roles.list_categories(session)


@router.get("/{slug}", response_model=RoleOut)
def get_role_by_slug(slug: str, session: Session = Depends(get_db_session)):
    """A single role by slug."""
    role = roles.get_role(session, slug)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{slug}' not found")
    return _out(role)
