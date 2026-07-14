"""Applications router — CRUD for the application pipeline."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from ..schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from packages.db.repositories import ApplicationRepository

router = APIRouter()


@router.get("/", response_model=List[ApplicationResponse])
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """List applications, optionally filtered by status."""
    repo = ApplicationRepository(session)
    if status:
        apps = repo.get_by_status(status=status, user_id=user_id)
    else:
        apps = repo.get_all(user_id=user_id)
    return [ApplicationResponse.model_validate(a) for a in apps]


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
    repo = ApplicationRepository(session)
    app = repo.upsert(
        url=data.url,
        title=data.title,
        company=data.company,
        status=data.status,
        user_id=user_id,
    )
    return ApplicationResponse.model_validate(app)


@router.put("/{url:path}", response_model=ApplicationResponse)
def update_application(
    url: str,
    data: ApplicationUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Advance application status."""
    repo = ApplicationRepository(session)
    app = repo.advance_status(
        url=url,
        new_status=data.status,
        notes=data.notes,
        user_id=user_id,
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(app)
