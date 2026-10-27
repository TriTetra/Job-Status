"""Briefing API — facts for the dashboard home page (copy is composed by the web app)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from careeros.briefing.facts import get_briefing_facts

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


@router.get("")
def get_briefing(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Top opportunities, evidence counts, hiring companies, last-24h changes, live applications."""
    return get_briefing_facts(session, user_id)
