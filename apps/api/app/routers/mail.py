"""Mailbox connection: employers' answers to applications, found and acted on.

Connect with an app password (IMAP, read-only), check now, confirm or dismiss what Aplio
wasn't sure about, and disconnect (which forgets everything found).
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.applications.mail import account, sync

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


class ConnectIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)
    host: Optional[str] = Field(default=None, max_length=253)


class ResolveIn(BaseModel):
    action: Literal["confirm", "dismiss"]
    kind: Optional[Literal["rejection", "interview", "offer", "acknowledgment"]] = None


@router.get("", summary="Mailbox connection and what was found in it")
def mail_status(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return account.status(session, user_id)


@router.post("/connect", summary="Connect a mailbox with an app password (tested before it is kept)")
def mail_connect(body: ConnectIn, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        return account.connect(session, user_id, body.email, body.password, body.host)
    except account.MailError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/check", summary="Check the mailbox now")
def mail_check(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    result = sync.check(session, user_id)
    session.commit()
    return {"result": result, **account.status(session, user_id)}


@router.post("/signals/{signal_id}", summary="Confirm or dismiss something found in the mailbox")
def mail_resolve(signal_id: int, body: ResolveIn, user_id: str = Depends(get_user_id),
                 session: Session = Depends(get_db_session)):
    try:
        return sync.resolve(session, user_id, signal_id, body.action, body.kind)
    except LookupError:
        raise HTTPException(status_code=404, detail="Not found")


@router.delete("", status_code=204, summary="Disconnect and forget everything found in the mailbox")
def mail_disconnect(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    account.disconnect(session, user_id)
