"""Applications router — CRUD for the application pipeline."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from ..schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from careeros.applications import pipeline
from careeros.applications.repositories.application_repo import STATUSES, ApplicationRepository

router = APIRouter()


@router.get("/")
def list_applications(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
) -> List[dict]:
    """Your board: every application you didn't pass on, with logo key, score and time in stage."""
    return pipeline.pipeline(session, user_id)


@router.get("/analytics")
def application_analytics(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
) -> dict:
    """Funnel, weekly pace, response rate and score vs outcome."""
    return pipeline.analytics(session, user_id)


@router.get("/summary")
def pipeline_summary(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Count per status bucket."""
    repo = ApplicationRepository(session)
    return repo.get_pipeline_summary(user_id=user_id)


@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(
    data: ApplicationCreate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Create or return existing application (upsert by URL)."""
    _check_status(data.status)
    repo = ApplicationRepository(session)
    app = repo.upsert(
        url=data.url,
        title=data.title,
        company=data.company,
        status=data.status,
        user_id=user_id,
        notes=data.notes or None,
    )
    return ApplicationResponse.model_validate(app)


def _check_status(status: Optional[str]) -> None:
    if status is not None and status not in STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {', '.join(STATUSES)}")


@router.put("/{url:path}", response_model=ApplicationResponse)
def update_application(
    url: str,
    data: ApplicationUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Move an application to a new status and/or change its notes."""
    _check_status(data.status)
    repo = ApplicationRepository(session)
    if data.status is not None:
        app = repo.advance_status(url=url, new_status=data.status, notes=data.notes, user_id=user_id)
    else:
        app = repo.set_notes(url=url, notes=data.notes, user_id=user_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(app)


@router.delete("/{url:path}", status_code=204)
def delete_application(
    url: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Stop tracking an application (added by mistake)."""
    if not ApplicationRepository(session).remove(url=url, user_id=user_id):
        raise HTTPException(status_code=404, detail="Application not found")
