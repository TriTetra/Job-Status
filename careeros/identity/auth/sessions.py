"""Server-side sessions.

The browser holds a random 256-bit token in an httpOnly cookie; the database
holds only its sha256, so a leaked table cannot be replayed. Sessions slide:
each use within the TTL extends them, at most once per REFRESH_AFTER.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from careeros.identity.models.auth import AuthSession
from careeros.identity.models.user import User

COOKIE_NAME = "careeros_session"
TTL = timedelta(days=30)
REFRESH_AFTER = timedelta(hours=12)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(session: Session, user_id: str, user_agent: str | None = None, ip: str | None = None) -> str:
    """Start a session and return the raw token for the cookie."""
    token = secrets.token_urlsafe(32)
    now = utcnow()
    session.add(AuthSession(
        token_hash=hash_token(token),
        user_id=user_id,
        created_at=now,
        last_seen_at=now,
        expires_at=now + TTL,
        user_agent=(user_agent or "")[:300] or None,
        ip=(ip or "")[:64] or None,
    ))
    session.flush()
    return token


def resolve_session(session: Session, token: str | None) -> Optional[str]:
    """The user id behind a cookie token, or None (unknown, expired, or user deactivated)."""
    if not token:
        return None
    row = session.get(AuthSession, hash_token(token))
    now = utcnow()
    if row is None or row.expires_at <= now:
        return None
    user = session.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    if now - row.last_seen_at >= REFRESH_AFTER:
        row.last_seen_at = now
        row.expires_at = now + TTL
    return row.user_id


def revoke_session(session: Session, token: str | None) -> None:
    if token:
        session.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).delete()


def revoke_all(session: Session, user_id: str) -> int:
    """Sign a user out everywhere (password change, deactivation)."""
    return session.query(AuthSession).filter(AuthSession.user_id == user_id).delete()


def purge_expired(session: Session) -> int:
    return session.query(AuthSession).filter(AuthSession.expires_at <= utcnow()).delete()
