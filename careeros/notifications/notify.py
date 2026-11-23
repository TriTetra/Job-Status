"""What Aplio tells a connected user on Telegram after each scheduled rescore:
new strong matches (APPLY) and applications that have waited two weeks for an answer.
Each job is mentioned once; nothing is sent when there is nothing new.
"""

import html
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from sqlalchemy.orm import Session

from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job
from careeros.notifications import telegram
from careeros.notifications.models import DEFAULT_PREFS, TelegramLink
from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

MAX_MATCHES = 5      # per message
MAX_REMINDERS = 5
KEEP_SENT = 800      # remembered keys per user


def _esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def _app_link(path: str) -> str:
    return get_settings().web_app_url.rstrip("/") + path


def strong_matches(session: Session, user_id: str, limit: int = 50) -> list[dict]:
    rows = (session.query(CareerScore, Job).join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None),
                    CareerScore.recommendation.ilike("APPLY%"))
            .order_by(CareerScore.career_score.desc()).limit(limit).all())
    return [{"url": j.url, "title": j.title, "company": j.company, "score": round(s.career_score or 0),
             "where": "Remote" if j.remote else (j.location or "")} for s, j in rows]


def matches_message(items: list[dict]) -> str:
    head = f"🎯 <b>{len(items)} new strong match{'es' if len(items) != 1 else ''}</b>"
    lines = []
    for it in items:
        link = _app_link("/inbox?job=" + quote(it["url"], safe=""))
        where = f" · {_esc(it['where'][:60])}" if it.get("where") else ""
        lines.append(f"<b>{_esc(it['title'])}</b>\n{_esc(it['company'])} · {it['score']}{where}\n<a href=\"{_esc(link)}\">Open in Aplio</a>")
    return head + "\n\n" + "\n\n".join(lines)


def reminders_message(items: list[dict]) -> str:
    lines = [f"• <b>{_esc(a['title'])}</b> · {_esc(a.get('company') or '')} · {a.get('days_in_status')} days" for a in items]
    return ("⏰ <b>Waiting for an answer</b>\n\n" + "\n".join(lines)
            + "\n\nA short, specific follow-up to the recruiter often gets one. "
            + f"<a href=\"{_esc(_app_link('/applications'))}\">Your applications</a>")


def notify_user(session: Session, user_id: str, now: Optional[datetime] = None) -> int:
    """Send what's new to this user's Telegram; returns how many messages went out."""
    from careeros.applications.pipeline import pipeline

    row = session.get(TelegramLink, user_id)
    if not (row and row.chat_id and telegram.available()):
        return 0
    prefs = {**DEFAULT_PREFS, **(row.prefs or {})}
    sent = list(row.sent or [])
    seen = set(sent)
    messages: list[tuple[str, list[str]]] = []

    if prefs.get("matches"):
        new = [m for m in strong_matches(session, user_id) if m["url"] not in seen][:MAX_MATCHES]
        if new:
            messages.append((matches_message(new), [m["url"] for m in new]))
    if prefs.get("reminders"):
        stale = [a for a in pipeline(session, user_id, now) if a["stale"] and f"remind:{a['url']}" not in seen][:MAX_REMINDERS]
        if stale:
            messages.append((reminders_message(stale), [f"remind:{a['url']}" for a in stale]))

    if prefs.get("report"):
        from careeros.applications.report import daily_report, report_text

        day_key = f"report:{(now or datetime.now(timezone.utc)).date().isoformat()}"
        if day_key not in seen:
            r = daily_report(session, user_id, now)
            if r["queue"] or r["active"] or r["learn"]:
                messages.append((report_text(r, get_settings().web_app_url.rstrip("/")), [day_key]))

    count = 0
    for text_, keys in messages:
        try:
            telegram.send(row.chat_id, text_)
        except telegram.TelegramError as e:
            logger.warning("Telegram notification to %s failed: %s", user_id, e)
            if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                row.chat_id = None  # the user blocked the bot: stop trying
            break
        sent.extend(keys)
        count += 1
    row.sent = sent[-KEEP_SENT:]
    session.commit()
    return count


def notify_all(user_ids: list[str]) -> None:
    """Scheduler hook: one session per user, failures logged, never raised."""
    from careeros.db.connection import db

    if not telegram.available():
        return
    for uid in user_ids:
        try:
            with db.session_scope() as s:
                n = notify_user(s, uid, datetime.now(timezone.utc))
            if n:
                logger.info("Telegram: %d message(s) to %s", n, uid)
        except Exception:
            logger.exception("Telegram notification failed for %s", uid)
