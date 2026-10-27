"""OAuth API — HTTP layer over GitHub account linking."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from services.identity_service.application import github_account
from services.identity_service.application.github_account import GitHubAccountError
from shared.config import get_settings

from ..dependencies import get_db_session, get_user_id

# Per-endpoint auth: /github/callback is a browser redirect from GitHub,
# authenticated by its single-use state token instead of a Clerk session.
router = APIRouter(prefix="/api/oauth", tags=["oauth"])


def _http_error(e: GitHubAccountError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/github/authorize")
def github_authorize(user_id: str = Depends(get_user_id)):
    """Start GitHub OAuth flow — redirect user to GitHub."""
    try:
        return RedirectResponse(url=github_account.authorize_url(user_id))
    except GitHubAccountError as e:
        raise _http_error(e)


@router.get("/github/callback")
def github_callback(code: str = Query(...), state: str = Query(...), session: Session = Depends(get_db_session)):
    """GitHub redirects here; exchange the code, store the token, send the browser back to onboarding."""
    try:
        github_account.complete_authorization(session, state, code)
    except GitHubAccountError as e:
        raise _http_error(e)
    return RedirectResponse(url=f"{get_settings().web_app_url}/onboarding?step=EVIDENCE&github=connected")


@router.get("/github/status")
def github_status(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Check if user has connected GitHub account."""
    return github_account.account_status(session, user_id)


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
