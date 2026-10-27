"""Jobs API — HTTP layer over job intelligence (opportunities, reasoning, scan)."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from careeros.jobs.models.career_score import CareerScore
from careeros.applications.repositories.application_repo import ApplicationRepository
from careeros.jobs import opportunities
from careeros.jobs import ingest
from careeros.jobs.scan import ALL_TIME_HOURS, run_scan, scan_jobs
from careeros.shared.background import JobForbidden, JobNotFound

from ..dependencies import get_db_session, get_user_id
from ..schemas.job import JobListResponse, JobWithScore

router = APIRouter()


def _serialize(s: CareerScore, user_decision: Optional[dict] = None) -> JobWithScore:
    rec = (s.recommendation or "CONSIDER").split(" - ")[0].strip().upper()
    if rec not in ("APPLY", "CONSIDER", "SKIP"):
        rec = "CONSIDER"
    return JobWithScore(
        url=s.url,
        career_score=s.career_score,
        fit_score=s.fit_score,
        acceptance_probability=s.acceptance_probability,
        career_value=s.career_value,
        market_demand=s.market_demand,
        expected_value=s.expected_value,
        recommendation=rec,
        skill_gaps=s.skill_gaps or [],
        explanation=s.explanation or {},
        scanned_at=s.scanned_at.isoformat() if s.scanned_at else None,
        user_decision=user_decision or opportunities.UNREVIEWED,
    )


@router.get("/", response_model=JobListResponse)
def list_jobs(
    recommendation: str = Query("ALL", description="APPLY | CONSIDER | SKIP | ALL"),
    limit: int = Query(200, le=500, description="Max opportunities to return"),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Scored opportunities (latest score per job), best first. `total` counts all matches, not just this page."""
    scores = opportunities.list_opportunities(session, user_id, recommendation, limit)
    decisions = opportunities.user_decisions(session, user_id)
    total = opportunities.count_opportunities(session, user_id, recommendation)
    return JobListResponse(total=total, jobs=[_serialize(s, decisions.get(s.url)) for s in scores])


@router.get("/pipeline", summary="Pipeline summary counts")
def pipeline_counts(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Return counts per recommendation bucket."""
    return ApplicationRepository(session).get_pipeline_summary(user_id=user_id)


@router.get("/reasoning/{url:path}")
def get_reasoning(url: str, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """On-demand reasoning: LLM first, template fallback; cached on the score."""
    decision = opportunities.get_or_create_reasoning(session, user_id, url)
    if decision is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"decision": decision}


# ── scan pipeline ─────────────────────────────────────────────────────────

@router.post("/scan")
def start_scan(
    background_tasks: BackgroundTasks,
    hours: int = Query(ALL_TIME_HOURS, ge=0, le=ALL_TIME_HOURS, description="Hours to look back"),
    limit: int = Query(500, ge=1, le=5000, description="Max jobs to (re)score in this run"),
    user_id: str = Depends(get_user_id),
):
    """Score open jobs that changed since your last scan. Poll GET /scan/{job_id}/status."""
    job = scan_jobs.create(user_id, label="scan")
    background_tasks.add_task(run_scan, job, user_id, hours, limit)
    return {"job_id": job.job_id, "status": job.status}


@router.get("/scan/{job_id}/status")
def scan_status(job_id: str, user_id: str = Depends(get_user_id)):
    """Poll scan progress and logs."""
    try:
        return scan_jobs.get_owned(job_id, user_id).to_dict()
    except JobNotFound:
        raise HTTPException(404, "Job not found")
    except JobForbidden:
        raise HTTPException(403, "Unauthorized")


# ── company boards ────────────────────────────────────────────────────────

@router.get("/boards", summary="Company boards and their last sync")
def list_boards(session: Session = Depends(get_db_session)):
    return {"boards": ingest.board_status(session)}


@router.post("/sync")
def start_sync(background_tasks: BackgroundTasks, user_id: str = Depends(get_user_id)):
    """Refresh every company board now, then rescore you. One sync at a time; poll GET /sync/{job_id}/status."""
    job, created = ingest.sync_jobs.create_unless_active(user_id, ingest.SYNC_LABEL)
    if created:
        background_tasks.add_task(ingest.run_sync_job, job, user_id)
    return {"job_id": job.job_id, "status": job.status, "already_running": not created}


@router.get("/sync/{job_id}/status")
def sync_status(job_id: str):
    """Sync progress. Shared across users: a sync holds no personal data until its final scan step."""
    try:
        job = ingest.sync_jobs.get(job_id)
    except JobNotFound:
        raise HTTPException(404, "Job not found")
    return job.to_dict()


@router.get("/{url:path}", response_model=JobWithScore)
def get_job(url: str, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Latest score for a specific job URL."""
    score = opportunities.get_opportunity(session, user_id, url)
    if not score:
        raise HTTPException(status_code=404, detail="Job not found")
    return _serialize(score, opportunities.user_decisions(session, user_id).get(score.url))
