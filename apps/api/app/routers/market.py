"""Market API — signals, summary, skill trends, and the shared refresh job."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from careeros.market.repositories.market_signal_repo import MarketSignalRepository
from careeros.market.refresh import refresh_jobs, run_refresh, start_refresh
from careeros.shared.background import JobNotFound

from ..dependencies import get_db_session, get_user_id
from ..schemas.market import MarketSignalResponse, MarketSummaryResponse, SkillTrendResponse

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


@router.post("/refresh")
def start_market_refresh(
    background_tasks: BackgroundTasks,
    hours: int = Query(168, ge=1, le=720, description="TechCrunch hours back (default: 7 days)"),
    user_id: str = Depends(get_user_id),
):
    """Start a background HN + TechCrunch refresh (or join the one already running).

    Poll GET /refresh/{job_id}/status for progress.
    """
    job, created = start_refresh(user_id)
    if created:
        background_tasks.add_task(run_refresh, job, hours)
    return {"job_id": job.job_id, "status": job.status}


@router.get("/refresh/{job_id}/status")
def refresh_status(job_id: str):
    """Poll market refresh progress (market data is global: any signed-in user may poll)."""
    try:
        return refresh_jobs.get(job_id).to_dict()
    except JobNotFound:
        raise HTTPException(404, "Refresh job not found")
