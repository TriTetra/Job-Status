"""Telegram notifications: connect, preferences, test message, and the bot's webhook.

The webhook is the one route here without a session: Telegram calls it, and it is
authenticated by the secret token Telegram echoes back (set with setWebhook).
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from careeros.notifications import links, telegram

from ..dependencies import get_db_session, get_user_id

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


class PrefsIn(BaseModel):
    matches: Optional[bool] = None
    reminders: Optional[bool] = None


@router.get("")
def telegram_status(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return links.status(session, user_id)


@router.post("/link")
def telegram_link(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """A one-time t.me link: open it, press Start, and this account is connected."""
    if not telegram.available():
        raise HTTPException(503, "Telegram isn't set up on this server")
    try:
        return {"url": links.start_link(session, user_id)}
    except telegram.TelegramError as e:
        raise HTTPException(502, f"Telegram didn't answer: {e}")


@router.put("/prefs")
def telegram_prefs(body: PrefsIn, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    return {"prefs": links.set_prefs(session, user_id, body.model_dump(exclude_none=True))}


@router.post("/test", status_code=204)
def telegram_test(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        links.send_test(session, user_id)
    except telegram.TelegramError as e:
        raise HTTPException(409, str(e))


@router.delete("", status_code=204)
def telegram_disconnect(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    links.disconnect(session, user_id)


@router.post("/webhook")
async def telegram_webhook(request: Request,
                           x_telegram_bot_api_secret_token: Optional[str] = Header(default=None)):
    if not telegram.secret_ok(x_telegram_bot_api_secret_token):
        raise HTTPException(403, "Forbidden")
    try:
        update = await request.json()
    except ValueError:
        return {"ok": True}
    from careeros.db.connection import db

    with db.session_scope() as s:
        links.handle_update(s, update if isinstance(update, dict) else {})
    return {"ok": True}  # always 200 once authenticated, so Telegram doesn't retry
