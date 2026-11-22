"""Evidence API — HTTP layer over careeros.evidence."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.evidence import items, portfolio, profiles
from careeros.evidence.aggregation import ranked_user_skills
from careeros.evidence.sources import list_sources

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


class PortfolioCrawlRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2000)


class ProfileConnectRequest(BaseModel):
    value: str = Field(min_length=1, max_length=300)  # username, id or profile link


@router.get("/items")
def get_evidence_items(
    source: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """User's evidence items (optional source filter), grouped for the review UI."""
    return items.list_for_review(session, user_id, source)


@router.delete("/items/{item_id}")
def delete_evidence_item(item_id: int, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Delete evidence item (user removes false positive)."""
    if not items.delete_item(session, user_id, item_id):
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return {"status": "deleted", "item_id": str(item_id)}


@router.get("/skills/aggregated")
def get_aggregated_skills(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Skills across all sources (CV, GitHub, portfolio) with weighted confidence, best first."""
    return {"skills": ranked_user_skills(user_id, session)}


@router.post("/portfolio/crawl")
def crawl_portfolio(
    request: PortfolioCrawlRequest,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Crawl portfolio website and create evidence items."""
    try:
        return portfolio.sync_portfolio_evidence(user_id, request.url, session)
    except portfolio.PortfolioCrawlError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolio/status")
def get_portfolio_status(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Check if user has connected portfolio."""
    return portfolio.portfolio_status(session, user_id)


@router.delete("/portfolio")
def disconnect_portfolio(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Disconnect portfolio and remove its evidence."""
    portfolio.disconnect_portfolio(session, user_id)
    return {"status": "disconnected"}


@router.get("/sources")
def get_evidence_sources(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Connection sources from the registry, recommended for the user's current role."""
    return list_sources(session, user_id)


@router.post("/profiles/{source_id}")
def connect_profile(
    source_id: str,
    request: ProfileConnectRequest,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Connect a public profile (GitHub, GitLab, Stack Overflow, ORCID, Medium, Substack) by username/link."""
    if source_id not in profiles.READERS:
        raise HTTPException(status_code=404, detail="This source can't be connected yet.")
    try:
        return profiles.connect_profile(session, user_id, source_id, request.value)
    except profiles.ProfileError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/profiles/{source_id}")
def disconnect_profile(source_id: str, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Forget a connected profile and remove its evidence."""
    if source_id not in profiles.READERS:
        raise HTTPException(status_code=404, detail="Unknown source")
    profiles.disconnect_profile(session, user_id, source_id)
    return {"status": "disconnected"}
