"""Briefing API — what changed since the last visit and what to do (copy is composed by the web app)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.briefing.digest import dismiss, get_digest

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


class DismissRequest(BaseModel):
    key: str = Field(min_length=1, max_length=200)


@router.get("")
def get_briefing(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Headline match, changes since the last visit, to-dos, this week's numbers."""
    return get_digest(session, user_id)


@router.post("/dismiss")
def dismiss_todo(body: DismissRequest, user_id: str = Depends(get_user_id),
                 session: Session = Depends(get_db_session)):
    """Hide one briefing to-do for a week."""
    dismiss(session, user_id, body.key)
    return {"status": "dismissed", "key": body.key}
