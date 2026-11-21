"""Auth API — sign in/out, who am I, first-account setup, invite links, own password.

No open sign-up: the first account is created through /setup (then closed), every
other one through an admin's single-use invite link.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.identity.auth import accounts, invites, sessions
from careeros.identity.auth.passwords import WeakPassword
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
    is_admin: bool


class NewAccountIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=1024)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class AcceptInviteIn(NewAccountIn):
    token: str = Field(..., min_length=10, max_length=200)


class TokenIn(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


class InviteCreateIn(BaseModel):
    email: Optional[str] = Field(None, max_length=320)


class InviteOut(BaseModel):
    id: str
    email: Optional[str]
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime]
    used_by_email: Optional[str]


class PasswordChangeIn(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=1024)
    new_password: str = Field(..., min_length=1, max_length=1024)


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


def _throttled(key: str, ip: str | None) -> None:
    wait = login_throttle.retry_after(key, ip)
    if wait:
        raise HTTPException(status_code=429, detail="Too many attempts — try again later",
                            headers={"Retry-After": str(wait)})


def _sign_in(response: Response, request: Request, session: Session, user_id: str) -> None:
    _set_cookie(response, sessions.create_session(
        session, user_id, request.headers.get("user-agent"), _client_ip(request)))


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session: Session = Depends(get_db_session)):
    sessions.revoke_session(session, request.cookies.get(sessions.COOKIE_NAME))
    response.delete_cookie(sessions.COOKIE_NAME, path="/")


@router.get("/me", response_model=MeOut)
def me(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return MeOut(id=user.id, email=user.email, first_name=user.first_name, last_name=user.last_name,
                 onboarding_state=user.onboarding_state, is_admin=user.is_admin)


# ── first account ─────────────────────────────────────────────────────────

@router.get("/setup")
def setup_status(session: Session = Depends(get_db_session)):
    """Whether this site still needs its first account (public: the sign-in page asks)."""
    return {"needed": invites.setup_needed(session)}


@router.post("/setup", status_code=204)
def setup(body: NewAccountIn, request: Request, response: Response, session: Session = Depends(get_db_session)):
    """Create the first account (it becomes admin) and sign in. Closed once any account exists."""
    _throttled(f"setup:{body.email}", _client_ip(request))
    try:
        user = invites.create_first_admin(session, body.email, body.password, body.first_name, body.last_name)
    except WeakPassword as e:
        raise HTTPException(status_code=400, detail=str(e))
    except accounts.AccountError as e:
        raise HTTPException(status_code=409, detail=str(e))
    _sign_in(response, request, session, user.id)


# ── invite links ──────────────────────────────────────────────────────────

@router.post("/invites/check")
def check_invite(body: TokenIn, request: Request, session: Session = Depends(get_db_session)):
    """Is this invite usable, and for which email (public: the invite page asks)."""
    ip = _client_ip(request)
    _throttled("invite-check", ip)
    invite = invites.check_invite(session, body.token)
    if invite is None:
        login_throttle.record_failure("invite-check", ip)
        return {"valid": False, "email": None}
    return {"valid": True, "email": invite.email}


@router.post("/invites/accept", status_code=204)
def accept_invite(body: AcceptInviteIn, request: Request, response: Response,
                  session: Session = Depends(get_db_session)):
    """Create an account from an invite link and sign in."""
    ip = _client_ip(request)
    _throttled("invite-accept", ip)
    try:
        user = invites.accept_invite(session, body.token, body.email, body.password,
                                     body.first_name, body.last_name)
    except WeakPassword as e:
        raise HTTPException(status_code=400, detail=str(e))
    except invites.InviteInvalid as e:
        login_throttle.record_failure("invite-accept", ip)
        raise HTTPException(status_code=410, detail=str(e))
    except accounts.AccountError as e:
        raise HTTPException(status_code=409, detail=str(e))
    _sign_in(response, request, session, user.id)


@router.get("/invites", response_model=list[InviteOut])
def list_invites(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        return [InviteOut(**vars(i)) for i in invites.list_invites(session, user_id)]
    except invites.NotAdmin as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/invites", status_code=201)
def create_invite(body: InviteCreateIn, user_id: str = Depends(get_user_id),
                  session: Session = Depends(get_db_session)):
    """A single-use sign-up link (7 days). The link is returned once; it can't be shown again."""
    try:
        invite, token = invites.create_invite(session, user_id, body.email or None)
    except invites.NotAdmin as e:
        raise HTTPException(status_code=403, detail=str(e))
    except accounts.AccountError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"id": invite.id, "email": invite.email, "expires_at": invite.expires_at,
            "url": f"{get_settings().web_app_url}/invite/{token}"}


@router.delete("/invites/{invite_id}", status_code=204)
def revoke_invite(invite_id: str, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    try:
        if not invites.revoke_invite(session, user_id, invite_id):
            raise HTTPException(status_code=404, detail="No pending invite with that id")
    except invites.NotAdmin as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── own password ──────────────────────────────────────────────────────────

@router.post("/password", status_code=204)
def change_password(body: PasswordChangeIn, request: Request, user_id: str = Depends(get_user_id),
                    session: Session = Depends(get_db_session)):
    """Change your password; every other browser is signed out, this one stays."""
    ip = _client_ip(request)
    _throttled(f"password:{user_id}", ip)
    try:
        invites.change_password(session, user_id, body.current_password, body.new_password,
                                request.cookies.get(sessions.COOKIE_NAME))
    except WeakPassword as e:
        raise HTTPException(status_code=400, detail=str(e))
    except accounts.AccountError as e:
        login_throttle.record_failure(f"password:{user_id}", ip)
        raise HTTPException(status_code=400, detail=str(e))
