"""Which CV was current: tagged on every application so outcomes can be tied to the CV sent.

Until CVs are versioned like git (docs/v1/PERSON_MEMORY.md, phase 4) the reference is the
uploaded document and its version number: "doc:<id>@v<version>".
"""

from typing import Optional

from sqlalchemy.orm import Session


def current_cv(session: Session, user_id: str) -> Optional[dict]:
    """{"document_id", "version", "filename", "ref"} of the primary CV, else the newest; None if none."""
    from careeros.evidence.models.resume_document import ResumeDocument

    doc = (session.query(ResumeDocument)
           .filter(ResumeDocument.user_id == user_id)
           .order_by(ResumeDocument.is_primary.desc(), ResumeDocument.created_at.desc())
           .first())
    if doc is None:
        return None
    return {"document_id": doc.id, "version": doc.version, "filename": doc.filename, "ref": cv_ref(doc.id, doc.version)}


def cv_ref(document_id: int, version: int) -> str:
    return f"doc:{document_id}@v{version}"
