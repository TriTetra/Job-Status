"""Check a person's mailbox for answers to their applications and act on them.

1. Headers of recent INBOX messages (read-only).
2. Keep only messages about one of their open applications (careeros/applications/mail/match.py).
3. Read those messages and classify them (careeros/applications/mail/classify.py).
4. A sure answer (LLM confidence >= AUTO_CONFIDENCE, one clear application, a forward move)
   moves the application: rejected / interview / offer, or applied when an acknowledgment
   shows a shortlisted job was sent. It is recorded as OutcomeObserved by "agent:mail".
   Anything less sure waits for the person to confirm. Acknowledgments and other mail are
   only noted, so they aren't read again.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from careeros.applications.mail import account
from careeros.applications.mail.classify import Verdict, classify
from careeros.applications.mail.match import AppRef, match, own_domains
from careeros.applications.mail.reader import Header, fetch_body, headers_since
from careeros.applications.models.application import Application
from careeros.applications.models.mail_signal import MailSignal
from careeros.jobs.models.job import Job

logger = logging.getLogger(__name__)

AUTO_CONFIDENCE = 0.85
LOOKBACK_DAYS = 60          # first check: answers to applications sent in the last two months
OVERLAP = timedelta(days=2)
OPEN = ("to_apply", "applied", "interview", "offer")
TARGET = {"rejection": "rejected", "interview": "interview", "offer": "offer", "acknowledgment": "applied"}
ORDER = {"to_apply": 0, "applied": 1, "interview": 2, "offer": 3, "rejected": 4}
ACTOR = "agent:mail"


def target_for(kind: str, current: str) -> Optional[str]:
    """The status this answer moves the application to, if it is a step forward."""
    to = TARGET.get(kind)
    if to is None or current not in ORDER:
        return None
    if to == "applied":
        return "applied" if current == "to_apply" else None
    if to == "rejected":
        return "rejected" if current in ("to_apply", "applied", "interview") else None
    return to if ORDER[to] > ORDER[current] else None


def open_apps(session: Session, user_id: str, now: datetime) -> list[AppRef]:
    rows = (session.query(Application, Job).outerjoin(Job, Job.url == Application.url)
            .filter(Application.user_id == user_id, Application.status.in_(OPEN)).all())
    cutoff = now - timedelta(days=150)
    out = []
    for app, job in rows:
        when = app.applied_at or app.updated_at
        if when is not None and when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when is not None and when < cutoff:
            continue
        domains = own_domains(job.company_domain if job else None, job.application_url if job else None, app.url)
        out.append(AppRef(url=app.url, title=app.title or "", company=app.company or (job.company if job else ""),
                          status=app.status, domains=domains))
    return [a for a in out if a.name or a.domains]


def _move(session: Session, user_id: str, url: str, to: str, at: Optional[datetime], signal_id: int,
          actor: str = ACTOR) -> Optional[str]:
    from careeros.applications.repositories.application_repo import ApplicationRepository

    repo = ApplicationRepository(session)
    app = repo._get_for_user(url=url, user_id=user_id)
    if app is None:
        return None
    before = app.status
    repo._move(app, to, at=at, actor=actor, source={"mail_signal": signal_id})
    if to in ("rejected", "interview", "offer") and app.response_days is None and app.applied_at and at:
        applied = app.applied_at if app.applied_at.tzinfo else app.applied_at.replace(tzinfo=timezone.utc)
        app.response_days = max(0, (at - applied).days)
    return before


def record(session: Session, user_id: str, h: Header, app: Optional[AppRef], v: Verdict, ambiguous: bool) -> MailSignal:
    """Store what was found and act on it when sure."""
    sig = MailSignal(user_id=user_id, message_key=h.key, url=app.url if app else None,
                     company=(app.company if app else None), title=(app.title[:500] if app else None),
                     received_at=h.date, from_domain=h.from_domain[:200], subject=h.subject[:300], kind=v.kind,
                     confidence=v.confidence, evidence=v.evidence[:300], state="noted")
    session.add(sig)
    session.flush()
    to = target_for(v.kind, app.status) if app else None
    sure = v.by == "llm" and v.confidence >= AUTO_CONFIDENCE and not ambiguous
    if to and sure:
        sig.status_before = _move(session, user_id, app.url, to, h.date, sig.id)
        sig.status_after, sig.state = to, "applied"
        app.status = to
    elif to or (v.kind == "info_request" and app):
        sig.state = "pending"        # the person confirms (or it asks them for something)
        sig.status_after = to
    return sig


def check(session: Session, user_id: str, now: Optional[datetime] = None,
          opener: Callable = account.open_mailbox, classifier: Callable = classify) -> dict:
    """One mailbox check. Returns counts; problems are kept on the connection, never raised."""
    now = now or datetime.now(timezone.utc)
    summary = {"read": 0, "about_applications": 0, "applied": 0, "pending": 0}
    creds = account.credentials(session, user_id)
    acc = account._account(session, user_id)
    if creds is None or acc is None:
        return summary
    apps = open_apps(session, user_id, now)
    if not apps:
        acc.last_synced_at, acc.sync_status = now, "ok"
        return summary
    since = (acc.last_synced_at - OVERLAP) if acc.last_synced_at else now - timedelta(days=LOOKBACK_DAYS)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    seen = {k for (k,) in session.query(MailSignal.message_key).filter(MailSignal.user_id == user_id).all()}
    try:
        conn = opener(*creds)
    except account.MailError as e:
        acc.sync_status = "sign_in_failed"
        logger.info("Mailbox check for %s: %s", user_id, e)
        return {**summary, "problem": str(e)}
    try:
        headers = headers_since(conn, since)
        summary["read"] = len(headers)
        for h in headers:
            if h.key in seen:
                continue
            m = match(h, apps)
            if m is None:
                continue  # not about an application: not read further, not kept
            seen.add(h.key)
            body = fetch_body(conn, h.uid)
            v = classifier(m.app.title, m.app.company, h.from_addr, h.subject, body)
            sig = record(session, user_id, h, m.app, v, m.ambiguous)
            summary["about_applications"] += 1
            summary[sig.state] = summary.get(sig.state, 0) + 1
    except Exception:
        logger.exception("Mailbox check failed for %s", user_id)
        acc.sync_status = "read_failed"
        return summary
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    acc.last_synced_at, acc.sync_status = now, "ok"
    return summary


def resolve(session: Session, user_id: str, signal_id: int, action: str, kind: Optional[str] = None) -> dict:
    """The person's answer to a pending signal: confirm it (optionally as another kind) or dismiss it."""
    sig = session.get(MailSignal, signal_id)
    if sig is None or sig.user_id != user_id:
        raise LookupError("not found")
    if action == "dismiss":
        sig.state = "dismissed"
    elif action == "confirm":
        if kind:
            sig.kind = kind
        app = session.query(Application).filter(Application.user_id == user_id, Application.url == sig.url).first() \
            if sig.url else None
        to = target_for(sig.kind, app.status) if app else None
        if to:
            sig.status_before = _move(session, user_id, sig.url, to, sig.received_at, sig.id, actor="user")
            sig.status_after = to
        sig.state = "applied" if to else "dismissed"
    else:
        raise ValueError("action must be confirm or dismiss")
    session.flush()
    return account.signal_dict(sig)


def check_all(user_ids: list[str]) -> None:
    """Scheduler hook: every connected mailbox, one session each; failures are logged."""
    from careeros.db.connection import db
    from careeros.identity.models.connected_account import ConnectedAccount

    with db.session_scope() as s:
        connected = {u for (u,) in s.query(ConnectedAccount.user_id).filter(
            ConnectedAccount.provider == account.PROVIDER, ConnectedAccount.is_active.is_(True)).all()}
    for uid in user_ids:
        if uid not in connected:
            continue
        try:
            with db.session_scope() as s:
                r = check(s, uid)
            if r.get("about_applications"):
                logger.info("Mailbox %s: %s", uid, r)
        except Exception:
            logger.exception("Mailbox check failed for %s", uid)
