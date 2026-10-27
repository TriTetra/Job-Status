"""Store an uploaded CV and run the PDF → evidence extraction job."""

import logging
import uuid
from pathlib import Path

from careeros.db.connection import db
from careeros.evidence.models.resume_document import ResumeDocument
from careeros.identity.repositories.user_repo import UserRepository
from careeros.identity.domain.onboarding import OnboardingState
from careeros.evidence.resume import process_resume
from careeros.shared.background import BackgroundJob
from careeros.shared.config import ROOT

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 25 * 1024 * 1024
UPLOAD_DIR = ROOT / "personal"  # gitignored


class UploadRejected(ValueError):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def store_resume_pdf(filename: str, content: bytes) -> Path:
    """Validate and save the upload (size checked before anything touches disk).

    Raises UploadRejected (400 wrong type / 413 too large).
    """
    if not (filename or "").lower().endswith(".pdf"):
        raise UploadRejected("Only PDF files are accepted", 400)
    if len(content) > MAX_PDF_BYTES:
        raise UploadRejected("PDF too large — max 25 MB", 413)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"resume_{uuid.uuid4()}.pdf"
    path.write_bytes(content)
    return path


def run_extraction(job: BackgroundJob, file_path: Path, user_id: str, filename: str) -> None:
    """Background task: PDF → LLM → evidence items, then advance onboarding to CONNECTIONS."""
    try:
        with db.session_scope() as session:
            resume_doc = ResumeDocument(
                user_id=user_id, filename=filename, storage_key=str(file_path), parse_status="pending",
            )
            session.add(resume_doc)
            session.commit()
            session.refresh(resume_doc)

            job.update(status="parsing", progress=15)
            summary = process_resume(resume_doc, session, log=job.log)

            job.progress = 90
            job.log("Updating profile state...")
            repo = UserRepository(session)
            repo.set_onboarding_state(user_id, OnboardingState.CONNECTIONS)
            repo.patch_profile_data(user_id, {"resume_path": str(file_path), "resume_doc_id": resume_doc.id})

            job.update(
                result={
                    "skills_extracted": summary["skills_count"],
                    "experience_count": summary["experience_count"],
                    "projects_count": summary["projects_count"],
                    "evidence_items": summary["skills_count"] + summary["experience_count"] + summary["projects_count"],
                },
                progress=100,
                status="completed",
            )
            job.log("Extraction complete — Career Graph ready")
    except Exception as exc:
        logger.exception("CV extraction failed for %s", user_id)
        job.fail(exc, f"Extraction failed: {exc}")
