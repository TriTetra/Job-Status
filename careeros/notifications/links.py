"""Connecting a user's Telegram: a one-time t.me link opens the bot, pressing Start sends
"/start <token>" to our webhook, and the token says which user the chat belongs to.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from careeros.notifications import telegram
from careeros.notifications.models import DEFAULT_PREFS, TelegramLink

LINK_TTL = timedelta(minutes=30)
PREF_KEYS = tuple(DEFAULT_PREFS)

HELP = ("I'm Aplio's notifier. I send you <b>new strong matches</b> and <b>follow-up reminders</b> "
        "for applications that are waiting.\n\nManage it in Aplio → Settings → Connections. Send /stop to disconnect.")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _prefs(row: Optional[TelegramLink]) -> dict:
    return {**DEFAULT_PREFS, **((row.prefs or {}) if row else {})}


def status(session: Session, user_id: str) -> dict:
    row = session.get(TelegramLink, user_id)
    connected = bool(row and row.chat_id)
    bot = None
    if telegram.available():
        try:
            bot = telegram.bot_username() or None
        except telegram.TelegramError:
            bot = None
    return {
        "available": telegram.available(),
        "bot": bot,
        "connected": connected,
        "username": row.username if connected else None,
        "linked_at": row.linked_at.isoformat() if connected and row.linked_at else None,
        "prefs": _prefs(row),
    }


def start_link(session: Session, user_id: str) -> str:
    """A t.me link that connects this user's Telegram when they press Start (valid 30 minutes)."""
    bot = telegram.bot_username()
    if not bot:
        raise telegram.TelegramError("The bot has no username")
    token = secrets.token_urlsafe(24)  # only A-Z a-z 0-9 _ -, as Telegram's start parameter needs
    row = session.get(TelegramLink, user_id)
    if row is None:
        row = TelegramLink(user_id=user_id, prefs=dict(DEFAULT_PREFS), sent=[])
        session.add(row)
    row.link_token_hash = _hash(token)
    row.link_expires_at = _now() + LINK_TTL
    session.commit()
    return f"https://t.me/{bot}?start={token}"


def disconnect(session: Session, user_id: str) -> None:
    row = session.get(TelegramLink, user_id)
    if row:
        row.chat_id, row.username, row.linked_at = None, None, None
        session.commit()


def set_prefs(session: Session, user_id: str, prefs: dict) -> dict:
    row = session.get(TelegramLink, user_id)
    if row is None:
        row = TelegramLink(user_id=user_id, prefs=dict(DEFAULT_PREFS), sent=[])
        session.add(row)
    row.prefs = {**_prefs(row), **{k: bool(v) for k, v in prefs.items() if k in PREF_KEYS}}
    session.commit()
    return _prefs(row)


def send_test(session: Session, user_id: str) -> None:
    row = session.get(TelegramLink, user_id)
    if not (row and row.chat_id):
        raise telegram.TelegramError("Telegram is not connected")
    telegram.send(row.chat_id, "✅ Aplio can reach you here. New strong matches and follow-up reminders will arrive in this chat.")


def _already_known(session: Session, user_id: str) -> list[str]:
    """What the user can already see in Aplio: marked as sent on connect, so the chat
    starts with what's new instead of every old match."""
    from careeros.applications.pipeline import pipeline
    from careeros.notifications.notify import strong_matches

    return ([m["url"] for m in strong_matches(session, user_id, limit=200)]
            + [f"remind:{a['url']}" for a in pipeline(session, user_id) if a["stale"]])


def _row_for_token(session: Session, token: str) -> Optional[TelegramLink]:
    return (session.query(TelegramLink)
            .filter(TelegramLink.link_token_hash == _hash(token), TelegramLink.link_expires_at > _now())
            .one_or_none())


def _rows_for_chat(session: Session, chat_id: int, exclude_user: Optional[str] = None) -> list[TelegramLink]:
    q = session.query(TelegramLink).filter(TelegramLink.chat_id == chat_id)
    if exclude_user:
        q = q.filter(TelegramLink.user_id != exclude_user)
    return q.all()


def handle_update(session: Session, update: dict) -> Optional[str]:
    """Act on one webhook update; returns the reply sent (or None). Only private chats count."""
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    if chat.get("type") != "private" or not chat.get("id"):
        return None
    chat_id, text = int(chat["id"]), (msg.get("text") or "").strip()
    command, _, arg = text.partition(" ")
    command = command.split("@", 1)[0].lower()

    if command == "/start" and arg.strip():
        row = _row_for_token(session, arg.strip())
        if row is None:
            reply = "That link has expired or was already used. Open Aplio → Settings → Connections and press Connect again."
        else:
            # A chat belongs to one Aplio account: free it from any other first
            for other in _rows_for_chat(session, chat_id, exclude_user=row.user_id):
                other.chat_id, other.username, other.linked_at = None, None, None
            session.flush()
            sender = msg.get("from") or {}
            row.chat_id = chat_id
            row.username = (sender.get("username") or sender.get("first_name") or "")[:64] or None
            row.linked_at = _now()
            row.link_token_hash, row.link_expires_at = None, None
            row.sent = list(dict.fromkeys([*(row.sent or []), *_already_known(session, row.user_id)]))[-800:]
            reply = "✅ Connected to Aplio. You'll get new strong matches and reminders for applications that wait too long.\n\nSend /stop to disconnect."
        session.commit()
    elif command in ("/stop", "/disconnect"):
        rows = _rows_for_chat(session, chat_id)
        for r in rows:
            r.chat_id, r.username, r.linked_at = None, None, None
        session.commit()
        reply = "Disconnected. You can connect again from Aplio → Settings → Connections." if rows else HELP
    else:
        reply = HELP
    try:
        telegram.send(chat_id, reply)
    except telegram.TelegramError:
        pass  # the link state is saved either way
    return reply
