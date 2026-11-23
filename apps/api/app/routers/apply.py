"""Ready to apply: today's queue, a prepared kit per job, and the daily report.

Aplio prepares; the person submits. Nothing here sends an application anywhere.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.applications import kit as apply_kit
from careeros.applications import queue as apply_queue
from careeros.applications.report import daily_report

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


@router.get("/queue", summary="Today's best jobs to send, with their kits when ready")
def get_queue(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return {"items": apply_queue.today(session, user_id)}


@router.get("/kit", summary="The prepared kit for one job, if there is one")
def get_kit(url: str = Query(..., max_length=2048), user_id: str = Depends(get_user_id),
            session: Session = Depends(get_db_session)):
    return {"kit": apply_kit.get_kit(session, user_id, url)}


class KitRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    refresh: bool = False


@router.post("/kit", summary="Prepare (or re-prepare) the kit for one job")
def prepare_kit(body: KitRequest, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        return {"kit": apply_kit.build_kit(session, user_id, body.url, refresh=body.refresh)}
    except apply_kit.UnknownJob:
        raise HTTPException(status_code=404, detail="This job is no longer available.")


@router.get("/report", summary="The daily report: applications, chances, today's queue, what to learn")
def get_report(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return daily_report(session, user_id)
