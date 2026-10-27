"""Account management (CLI) and authentication (API login)."""

import secrets
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from careeros.identity.auth import passwords, sessions
from careeros.identity.models.auth import AuthCredential
from careeros.identity.models.user import User
from careeros.identity.repositories.user_repo import UserRepository


class AccountError(ValueError):
    pass


@dataclass(frozen=True)
class AccountInfo:
    id: str
    email: str
    name: str
    is_active: bool
    has_password: bool
    onboarding_state: str


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise AccountError(f"Not an email address: {email!r}")
    return email


def new_user_id() -> str:
    return f"user_{secrets.token_hex(12)}"


def create_account(session: Session, email: str, password: str,
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    email = normalize_email(email)
    if UserRepository(session).get_by_email(email):
        raise AccountError(f"{email} already has an account — use `career-os user passwd` to set a password")
    password_hash = passwords.hash_password(password)
    user = UserRepository(session).create_user(user_id=new_user_id(), email=email,
                                               first_name=first_name, last_name=last_name)
    session.add(AuthCredential(user_id=user.id, password_hash=password_hash))
    session.flush()
    return user


def set_password(session: Session, email: str, password: str) -> User:
    """Set or replace a password (also how users migrated from Clerk get one). Signs out everywhere."""
    user = UserRepository(session).get_by_email(normalize_email(email))
    if user is None:
        raise AccountError(f"No user with email {email}")
    password_hash = passwords.hash_password(password)
    cred = session.get(AuthCredential, user.id)
    if cred is None:
        session.add(AuthCredential(user_id=user.id, password_hash=password_hash))
    else:
        cred.password_hash = password_hash
        cred.password_changed_at = sessions.utcnow()
    sessions.revoke_all(session, user.id)
    session.flush()
    return user


def set_active(session: Session, email: str, active: bool) -> User:
    user = UserRepository(session).get_by_email(normalize_email(email))
    if user is None:
        raise AccountError(f"No user with email {email}")
    user.is_active = active
    if not active:
        sessions.revoke_all(session, user.id)
    session.flush()
    return user


def authenticate(session: Session, email: str, password: str) -> Optional[User]:
    """The user if email + password match an active account, else None (same cost either way)."""
    try:
        email = normalize_email(email)
    except AccountError:
        passwords.verify_password(None, password)
        return None
    user = UserRepository(session).get_by_email(email)
    cred = session.get(AuthCredential, user.id) if user else None
    ok = passwords.verify_password(cred.password_hash if cred else None, password)
    if not ok or user is None or not user.is_active:
        return None
    if passwords.needs_rehash(cred.password_hash):
        cred.password_hash = passwords.hash_password(password)
    return user


def list_accounts(session: Session) -> list[AccountInfo]:
    with_password = {uid for (uid,) in session.query(AuthCredential.user_id).all()}
    return [
        AccountInfo(u.id, u.email, u.display_name, u.is_active, u.id in with_password, u.onboarding_state)
        for u in session.query(User).order_by(User.created_at).all()
    ]
