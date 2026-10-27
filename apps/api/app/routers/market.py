"""Market intelligence router."""

import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session
from ..schemas.market import MarketSignalResponse, MarketSummaryResponse, SkillTrendResponse
from core.db.repositories import MarketSignalRepository

router = APIRouter()

# In-memory refresh job store (production'da Redis)
refresh_jobs: dict[str, dict] = {}


def _run_refresh(job_id: str, hours: int) -> None:
    job = refresh_jobs[job_id]

    def log(msg: str) -> None:
        import datetime
        job["logs"].append({"ts": datetime.datetime.utcnow().isoformat(), "message": msg})

    try:
        job.update(status="running", progress=10)

        # HackerNews — this month's "Who is Hiring?" thread
        try:
            from plugins.market_signals.hackernews.signal_extractor import HNSignalExtractor
            import datetime
            now = datetime.datetime.utcnow()
            log("Scanning HackerNews Who is Hiring…")
            count = HNSignalExtractor().extract_monthly_signals(now.year, now.month)
            log(f"✓ HackerNews: {count} signals")
        except Exception as e:
            log(f"⚠ HackerNews skipped: {e}")

        job.update(progress=60)

        # TechCrunch — recent funding / layoff articles
        try:
            from plugins.market_signals.techcrunch.signal_extractor import TechCrunchSignalExtractor
            log(f"Scanning TechCrunch (last {hours}h)…")
            count = TechCrunchSignalExtractor().extract_signals(hours=hours)
            log(f"✓ TechCrunch: {count} signals")
        except Exception as e:
            log(f"⚠ TechCrunch skipped: {e}")

        job.update(status="completed", progress=100)
        log("✓ Refresh complete")

    except Exception as e:
        job.update(status="failed", error=str(e))
        log(f"✗ {e}")


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
def start_refresh(
    background_tasks: BackgroundTasks,
    hours: int = Query(168, ge=1, le=720, description="TechCrunch hours back (default: 7 days)"),
):
    """
    Start a background HN + TechCrunch refresh.
    Poll GET /refresh/{job_id}/status for progress.

    Market data is global, so at most one refresh runs at a time: a second
    request returns the in-flight job instead of starting another crawl.
    """
    in_flight = next(
        (j for j in refresh_jobs.values() if j["status"] in ("pending", "running")), None
    )
    if in_flight:
        return {"job_id": in_flight["job_id"], "status": in_flight["status"]}

    job_id = str(uuid.uuid4())
    refresh_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "error": None,
    }
    background_tasks.add_task(_run_refresh, job_id, hours)
    return {"job_id": job_id, "status": "pending"}


@router.get("/refresh/{job_id}/status")
def refresh_status(job_id: str):
    """Poll market refresh progress."""
    job = refresh_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Refresh job not found")
    return job

