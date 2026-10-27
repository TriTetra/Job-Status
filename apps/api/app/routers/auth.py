"""Auth API — sign in, sign out, who am I. No sign-up: accounts come from `career-os user add`."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.identity.auth import accounts, sessions
from careeros.identity.auth.throttle import login_throttle
from careeros.identity.repositories.user_repo import UserRepository
from careeros.shared.config import get_settings

from ..dependencies import get_db_session, get_user_id

router = APIRouter()


class LoginIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=1024)


class MeOut(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    onboarding_state: str


def _client_ip(request: Request) -> str | None:
    # uvicorn runs with --proxy-headers behind Coolify's proxy, so this is the real client
    return request.client.host if request.client else None


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        sessions.COOKIE_NAME,
        token,
        max_age=int(sessions.TTL.total_seconds()),
        httponly=True,                                  # not readable from JavaScript
        secure=get_settings().session_cookie_secure,
        samesite="lax",                                 # not sent on cross-site POSTs
        path="/",
    )


@router.post("/login", status_code=204)
def login(body: LoginIn, request: Request, response: Response, session: Session = Depends(get_db_session)):
    ip = _client_ip(request)
    wait = login_throttle.retry_after(body.email, ip)
    if wait:
        raise HTTPException(status_code=429, detail="Too many attempts — try again later",
                            headers={"Retry-After": str(wait)})

    user = accounts.authenticate(session, body.email, body.password)
    if user is None:
        login_throttle.record_failure(body.email, ip)
        raise HTTPException(status_code=401, detail="Wrong email or password")

    login_throttle.record_success(body.email)
    sessions.purge_expired(session)
    _set_cookie(response, sessions.create_session(session, user.id, request.headers.get("user-agent"), ip))


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session: Session = Depends(get_db_session)):
    sessions.revoke_session(session, request.cookies.get(sessions.COOKIE_NAME))
    response.delete_cookie(sessions.COOKIE_NAME, path="/")


@router.get("/me", response_model=MeOut)
def me(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return MeOut(id=user.id, email=user.email, first_name=user.first_name,
                 last_name=user.last_name, onboarding_state=user.onboarding_state)
