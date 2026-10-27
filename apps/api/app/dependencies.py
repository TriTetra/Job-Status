"""FastAPI dependencies — DB session and user identity."""

import logging
import os
from typing import Generator, Optional

from fastapi import Header, HTTPException, Request

from core.db.connection import db
from .core.auth.clerk_auth import ClerkAuthenticator

logger = logging.getLogger(__name__)

# Opt-in only (local e2e scripts): lets `X-User-Id: user_e2e_*` act as a user
# without a Clerk token. Must never be set in a deployed environment.
E2E_BYPASS_ENV = "CAREEROS_E2E_AUTH_BYPASS"
E2E_USER_PREFIX = "user_e2e_"


def get_db_session() -> Generator:
    with db.session_scope() as session:
        yield session


def _verify(token: str, source: str) -> str:
    try:
        return ClerkAuthenticator.verify_token(token)
    except Exception as e:
        logger.info("Rejected %s token: %s", source, e)
        raise HTTPException(status_code=401, detail="Invalid authentication token")


def get_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(default=None),
) -> str:
    """Resolve the Clerk user id for this request, or raise 401.

    Order: Bearer token → Clerk `__session` cookie → opt-in e2e header.
    There is no anonymous fallback.
    """
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return _verify(auth[7:], "bearer")

    session_token = request.cookies.get("__session")
    if session_token:
        return _verify(session_token, "cookie")

    if (
        x_user_id
        and x_user_id.startswith(E2E_USER_PREFIX)
        and os.getenv(E2E_BYPASS_ENV) == "1"
    ):
        return x_user_id

    raise HTTPException(status_code=401, detail="Authentication required")
