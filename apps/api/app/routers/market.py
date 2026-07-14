"""Market intelligence router."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session
from ..schemas.market import MarketSignalResponse, MarketSummaryResponse, SkillTrendResponse
from packages.db.repositories import MarketSignalRepository

router = APIRouter()


@router.get("/signals", response_model=List[MarketSignalResponse])
def list_signals(
    days: int = Query(7, description="Days to look back"),
    limit: int = Query(50, le=200),
    session: Session = Depends(get_db_session),
):
    """Recent market signals."""
    repo = MarketSignalRepository(session)
    signals = repo.get_recent(days=days, limit=limit)
    return [MarketSignalResponse.model_validate(s) for s in signals]


@router.get("/summary", response_model=MarketSummaryResponse)
def market_summary(
    days: int = Query(7, description="Days to summarize"),
    session: Session = Depends(get_db_session),
):
    """Aggregate market summary: signal counts, top companies, top skills."""
    repo = MarketSignalRepository(session)
    return MarketSummaryResponse(**repo.get_market_summary(days=days))


@router.get("/trend/{skill}", response_model=SkillTrendResponse)
def skill_trend(
    skill: str,
    days: int = Query(30, description="Days to analyze"),
    session: Session = Depends(get_db_session),
):
    """Skill demand trend compared to previous period."""
    repo = MarketSignalRepository(session)
    return SkillTrendResponse(**repo.get_skill_trend(skill_name=skill, days=days))
