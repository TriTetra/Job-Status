"""FastAPI dependencies — DB session and the signed-in user."""

import logging
from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from careeros.db.connection import db
from careeros.identity.auth.sessions import COOKIE_NAME, resolve_session
from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

# Opt-in only (local e2e scripts): CAREEROS_E2E_AUTH_BYPASS=1 lets
# `X-User-Id: user_e2e_*` act as a user without a session.
# Must never be set in a deployed environment.
E2E_USER_PREFIX = "user_e2e_"


def get_db_session() -> Generator:
    with db.session_scope() as session:
        yield session


def get_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(default=None),
    session: Session = Depends(get_db_session),
) -> str:
    """The signed-in user's id from the session cookie, or 401. There is no anonymous fallback."""
    user_id = resolve_session(session, request.cookies.get(COOKIE_NAME))
    if user_id:
        return user_id

    if x_user_id and x_user_id.startswith(E2E_USER_PREFIX) and get_settings().e2e_auth_bypass:
        return x_user_id

    raise HTTPException(status_code=401, detail="Authentication required")
