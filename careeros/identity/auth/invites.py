"""Web sign-up for a private site: the first account (setup) and invite links after that.

- While no account has a password, /sign-in offers "create your account"; that
  first account becomes admin. After that, setup is closed for good.
- An admin creates single-use invite links (7 days, optionally bound to one
  email). Only the token's sha256 is stored, like session tokens.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from careeros.identity.auth import accounts, passwords, sessions
from careeros.identity.auth.accounts import AccountError
from careeros.identity.models.auth import AuthCredential, AuthInvite
from careeros.identity.models.user import User

INVITE_TTL = timedelta(days=7)
_SETUP_LOCK = 0x5E7_0B  # pg advisory lock: two browsers racing to be the first account


class InviteInvalid(AccountError):
    """Unknown, used, expired or revoked invite."""


class NotAdmin(PermissionError):
    pass


@dataclass(frozen=True)
class InviteInfo:
    id: str
    email: Optional[str]
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime]
    used_by_email: Optional[str]


# ── setup ──────────────────────────────────────────────────────────────────

def setup_needed(session: Session) -> bool:
    """True until the first account with a password exists."""
    return session.query(AuthCredential.user_id).first() is None


def create_first_admin(session: Session, email: str, password: str,
                       first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _SETUP_LOCK})
    if not setup_needed(session):
        raise AccountError("This site already has an owner — ask them for an invite link")
    user = accounts.create_account(session, email, password, first_name, last_name)
    user.is_admin = True
    session.flush()
    return user


# ── invites ────────────────────────────────────────────────────────────────

def require_admin(session: Session, user_id: str) -> User:
    user = session.get(User, user_id)
    if user is None or not user.is_admin or not user.is_active:
        raise NotAdmin("Only admins can manage invites")
    return user


def create_invite(session: Session, admin_id: str, email: Optional[str] = None) -> tuple[AuthInvite, str]:
    """(invite, raw token). The token is shown once; the database keeps only its hash."""
    require_admin(session, admin_id)
    email = accounts.normalize_email(email) if email else None
    if email and session.query(User.id).filter(User.email == email).first():
        raise AccountError(f"{email} already has an account")
    token = secrets.token_urlsafe(32)
    invite = AuthInvite(
        id=secrets.token_hex(8), token_hash=sessions.hash_token(token), email=email,
        created_by=admin_id, expires_at=sessions.utcnow() + INVITE_TTL,
    )
    session.add(invite)
    session.flush()
    return invite, token


def _valid(session: Session, token: Optional[str], *, lock: bool = False) -> Optional[AuthInvite]:
    if not token:
        return None
    q = session.query(AuthInvite).filter(AuthInvite.token_hash == sessions.hash_token(token))
    invite = (q.with_for_update() if lock else q).first()
    if invite is None or invite.used_at is not None or invite.expires_at <= sessions.utcnow():
        return None
    return invite


def check_invite(session: Session, token: Optional[str]) -> Optional[AuthInvite]:
    return _valid(session, token)


def accept_invite(session: Session, token: str, email: str, password: str,
                  first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    invite = _valid(session, token, lock=True)  # row lock: a link can't be used twice at once
    if invite is None:
        raise InviteInvalid("This invite link is invalid, used or expired — ask for a new one")
    email = accounts.normalize_email(email)
    if invite.email and invite.email != email:
        raise InviteInvalid(f"This invite is for {invite.email}")
    user = accounts.create_account(session, email, password, first_name, last_name)
    invite.used_at, invite.used_by = sessions.utcnow(), user.id
    session.flush()
    return user


def list_invites(session: Session, admin_id: str) -> list[InviteInfo]:
    """Pending and used invites, newest first (expired unused ones are dropped)."""
    require_admin(session, admin_id)
    now = sessions.utcnow()
    session.query(AuthInvite).filter(AuthInvite.used_at.is_(None), AuthInvite.expires_at <= now).delete()
    emails = dict(session.query(User.id, User.email).all())
    rows = session.query(AuthInvite).order_by(AuthInvite.created_at.desc()).limit(50).all()
    return [InviteInfo(i.id, i.email, i.created_at, i.expires_at, i.used_at, emails.get(i.used_by)) for i in rows]


def revoke_invite(session: Session, admin_id: str, invite_id: str) -> bool:
    require_admin(session, admin_id)
    return bool(
        session.query(AuthInvite).filter(AuthInvite.id == invite_id, AuthInvite.used_at.is_(None)).delete()
    )


# ── own password ───────────────────────────────────────────────────────────

def change_password(session: Session, user_id: str, current: str, new: str, keep_token: Optional[str]) -> None:
    """Verify the current password, set the new one, sign out every other browser."""
    cred = session.get(AuthCredential, user_id)
    if cred is None or not passwords.verify_password(cred.password_hash, current):
        raise AccountError("Current password is wrong")
    if current == new:
        raise AccountError("Choose a password you haven't used here")
    cred.password_hash = passwords.hash_password(new)
    cred.password_changed_at = sessions.utcnow()
    sessions.revoke_others(session, user_id, keep_token)
    session.flush()
