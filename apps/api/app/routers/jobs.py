"""Jobs router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from ..schemas.job import JobListResponse, JobWithScore
from packages.db.repositories import CareerScoreRepository

router = APIRouter()


@router.get("/", response_model=JobListResponse)
def list_jobs(
    min_score: float = Query(60.0, description="Minimum career score"),
    recommendation: str = Query("APPLY", description="APPLY, CONSIDER, SKIP"),
    limit: int = Query(20, le=100),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Top job opportunities for the user."""
    repo = CareerScoreRepository(session)
    scores = repo.get_top_opportunities(
        min_score=min_score,
        recommendation=recommendation,
        limit=limit,
        user_id=user_id,
    )
    jobs = [
        JobWithScore(
            url=s.url,
            career_score=s.career_score,
            fit_score=s.fit_score,
            acceptance_probability=s.acceptance_probability,
            career_value=s.career_value,
            market_demand=s.market_demand,
            expected_value=s.expected_value,
            recommendation=s.recommendation,
            skill_gaps=s.skill_gaps or [],
            explanation=s.explanation or {},
            scanned_at=s.scanned_at.isoformat() if s.scanned_at else None,
        )
        for s in scores
    ]
    return JobListResponse(total=len(jobs), jobs=jobs)


@router.get("/pipeline", summary="Pipeline summary counts")
def pipeline_counts(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Return counts per recommendation bucket."""
    from packages.db.repositories import ApplicationRepository
    repo = ApplicationRepository(session)
    return repo.get_pipeline_summary(user_id=user_id)


@router.get("/{url:path}", response_model=JobWithScore)
def get_job(
    url: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Latest score for a specific job URL."""
    repo = CareerScoreRepository(session)
    score = repo.get_latest_score(url=url, user_id=user_id)
    if not score:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobWithScore(
        url=score.url,
        career_score=score.career_score,
        fit_score=score.fit_score,
        acceptance_probability=score.acceptance_probability,
        career_value=score.career_value,
        market_demand=score.market_demand,
        expected_value=score.expected_value,
        recommendation=score.recommendation,
        skill_gaps=score.skill_gaps or [],
        explanation=score.explanation or {},
        scanned_at=score.scanned_at.isoformat() if score.scanned_at else None,
    )
