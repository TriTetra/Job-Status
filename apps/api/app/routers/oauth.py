"""OAuth API — HTTP layer over GitHub account linking."""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from careeros.identity import github_account
from careeros.identity.github_account import GitHubAccountError

from ..dependencies import get_db_session, get_user_id

logger = logging.getLogger(__name__)

# Per-endpoint auth: /github/callback is a browser redirect from GitHub,
# authenticated by its single-use state token instead of a session cookie.
router = APIRouter(prefix="/api/oauth", tags=["oauth"])


def _http_error(e: GitHubAccountError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/github/authorize")
def github_authorize(
    return_to: Literal["onboarding", "settings"] = Query("onboarding"),
    user_id: str = Depends(get_user_id),
):
    """Start GitHub OAuth — a browser navigation, so failures go back to the page, not to JSON."""
    try:
        return RedirectResponse(url=github_account.authorize_url(user_id, return_to))
    except GitHubAccountError:
        return RedirectResponse(url=github_account.return_url(f"x.{return_to}", "unavailable"))


@router.get("/github/callback")
def github_callback(
    background: BackgroundTasks,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    session: Session = Depends(get_db_session),
):
    """GitHub redirects here; store the token, analyse the repos in the background, go back."""
    if error or not code or not state:  # e.g. the user pressed "Cancel" on GitHub
        return RedirectResponse(url=github_account.return_url(state, "cancelled"))
    try:
        user_id = github_account.complete_authorization(session, state, code)
    except GitHubAccountError as e:
        logger.info("GitHub callback failed: %s", e)
        return RedirectResponse(url=github_account.return_url(state, "error"))
    background.add_task(github_account.sync_in_background, user_id)
    return RedirectResponse(url=github_account.return_url(state, "connected"))


@router.get("/github/status")
def github_status(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Whether GitHub is connected, and whether it can be (OAuth app configured)."""
    return {**github_account.account_status(session, user_id), "available": github_account.configured()}


@router.delete("/github")
def github_disconnect(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Disconnect GitHub account."""
    github_account.disconnect(session, user_id)
    return {"status": "disconnected"}


@router.post("/github/sync")
def github_sync(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Sync GitHub repos and extract skill evidence."""
    try:
        return github_account.sync_evidence(session, user_id)
    except GitHubAccountError as e:
        raise _http_error(e)
