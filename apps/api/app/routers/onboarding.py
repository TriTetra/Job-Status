"""Onboarding API — HTTP layer over careeros.onboarding."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from careeros.identity.repositories.user_repo import UserRepository
from careeros.evidence.items import count_for_user
from careeros.onboarding import onboarding_jobs, profile
from careeros.onboarding.career_graph import run_graph_building
from careeros.onboarding.resume_upload import MAX_PDF_BYTES, UploadRejected, run_extraction, store_resume_pdf
from careeros.shared.background import JobForbidden, JobNotFound

from ..dependencies import get_db_session, get_user_id
from ..schemas.onboarding import GoalsPayload, IdentityPayload, OnboardingStateOut

router = APIRouter()


def _job_status(job_id: str, user_id: str) -> dict:
    try:
        return onboarding_jobs.get_owned(job_id, user_id).to_dict()
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found")
    except JobForbidden:
        raise HTTPException(status_code=403, detail="Unauthorized")


# ── profile + state machine ───────────────────────────────────────────────

@router.get("/state", response_model=OnboardingStateOut)
def get_onboarding_state(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return OnboardingStateOut(**profile.get_state(session, user_id))


@router.get("/identity")
def get_identity(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """The saved identity step (name, role, level, …) — used by the settings profile tab."""
    return profile.get_identity(session, user_id)


@router.post("/identity")
def save_identity(data: IdentityPayload, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    state = profile.save_identity(session, user_id, data.model_dump())
    return {"state": state, "message": "Identity saved"}


@router.post("/goals")
def save_goals(data: GoalsPayload, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        state = profile.save_goals(session, user_id, data.model_dump())
    except profile.OnboardingInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"state": state, "message": "Goals saved"}


@router.post("/advance")
def advance_state(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Manually advance to next state (EVIDENCE → CONNECTIONS → BUILDING → READY)."""
    return {"state": profile.advance(session, user_id)}


@router.post("/complete")
def complete_onboarding(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return {"state": profile.complete(session, user_id), "message": "Onboarding complete"}


# ── CV upload → evidence extraction ───────────────────────────────────────

@router.post("/resume")
def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
):
    """Upload resume PDF and start extraction job."""
    content = file.file.read(MAX_PDF_BYTES + 1)  # never buffer more than the limit
    try:
        path = store_resume_pdf(file.filename, content)
    except UploadRejected as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    job = onboarding_jobs.create(user_id, label=file.filename)
    background_tasks.add_task(run_extraction, job, path, user_id, file.filename)
    return {"job_id": job.job_id, "status": job.status}


@router.get("/resume/{job_id}/status")
def get_extraction_status(job_id: str, user_id: str = Depends(get_user_id)):
    """Poll extraction job status."""
    return _job_status(job_id, user_id)


# ── Career Graph ──────────────────────────────────────────────────────────

@router.post("/build-graph")
def build_career_graph(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Build Career Graph from extracted evidence items."""
    if not UserRepository(session).get_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not count_for_user(session, user_id):
        raise HTTPException(status_code=400, detail="No evidence items found. Upload resume first.")

    job = onboarding_jobs.create(user_id, label="career_graph")
    background_tasks.add_task(run_graph_building, job, user_id)
    return {"job_id": job.job_id, "status": job.status}


@router.get("/build-graph/{job_id}/status")
def get_graph_building_status(job_id: str, user_id: str = Depends(get_user_id)):
    """Poll graph building job status."""
    return _job_status(job_id, user_id)


@router.get("/career-graph")
def get_career_graph(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Get user's Career Graph nodes and edges."""
    return profile.get_career_graph(session, user_id)
