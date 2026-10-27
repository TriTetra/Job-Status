"""OAuth endpoints for third-party integrations (GitHub, etc.)."""

import secrets
from urllib.parse import urlencode
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from shared.config import get_settings

from ..dependencies import get_db_session, get_user_id
from ..core.auth.token_encryption import token_encryption
from core.db.models.connected_account import ConnectedAccount


router = APIRouter(prefix="/api/oauth", tags=["oauth"])


# ─── In-memory state store (production'da Redis kullan) ──────────
# CSRF koruması için state token'ları geçici sakla
oauth_states: dict[str, dict] = {}


# ─── GitHub OAuth ─────────────────────────────────────────────────

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_SCOPES = "read:user user:email repo"


@router.get("/github/authorize")
def github_authorize(
    user_id: str = Depends(get_user_id),
):
    """Start GitHub OAuth flow — redirect user to GitHub."""
    client_id = get_settings().github_client_id
    redirect_uri = get_settings().github_redirect_uri
    
    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured"
        )
    
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Clean up old states (>10 min)
    cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    for s in list(oauth_states.keys()):
        if oauth_states[s]["created_at"] < cutoff:
            del oauth_states[s]
    
    # Build authorization URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": GITHUB_SCOPES,
        "state": state,
    }
    
    auth_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: Session = Depends(get_db_session),
):
    """Handle GitHub OAuth callback — exchange code for token."""
    # Verify state (CSRF protection)
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    user_id = oauth_states[state]["user_id"]
    del oauth_states[state]
    
    # Exchange code for access token
    client_id = get_settings().github_client_id
    client_secret = get_settings().github_client_secret
    redirect_uri = get_settings().github_redirect_uri
    
    token_response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )
    
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"GitHub token exchange failed: {token_response.text}"
        )
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail=f"No access_token in response: {token_data}"
        )
    
    # Fetch GitHub user info
    user_response = requests.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=10,
    )
    
    if user_response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch GitHub user info"
        )
    
    github_user = user_response.json()
    
    # Encrypt token before storage
    encrypted_token = token_encryption.encrypt(access_token)
    
    # Upsert connected account
    existing = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github"
    ).first()
    
    if existing:
        existing.provider_user_id = str(github_user["id"])
        existing.provider_username = github_user["login"]
        existing.access_token = encrypted_token
        existing.account_metadata = {
            "avatar_url": github_user.get("avatar_url"),
            "public_repos": github_user.get("public_repos", 0),
            "followers": github_user.get("followers", 0),
            "bio": github_user.get("bio"),
        }
        existing.last_synced_at = datetime.utcnow()
    else:
        new_account = ConnectedAccount(
            user_id=user_id,
            provider="github",
            provider_user_id=str(github_user["id"]),
            provider_username=github_user["login"],
            access_token=encrypted_token,
            account_metadata={
                "avatar_url": github_user.get("avatar_url"),
                "public_repos": github_user.get("public_repos", 0),
                "followers": github_user.get("followers", 0),
                "bio": github_user.get("bio"),
            },
            last_synced_at=datetime.utcnow(),
        )
        session.add(new_account)

    session.commit()

    # Redirect back to frontend with success
    return RedirectResponse(
        url="http://localhost:3000/onboarding?step=EVIDENCE&github=connected"
    )


@router.get("/github/status")
def github_status(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Check if user has connected GitHub account."""
    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github"
    ).first()

    if not account:
        return {"connected": False}

    return {
        "connected": True,
        "username": account.provider_username,
        "provider_user_id": account.provider_user_id,
        "metadata": account.account_metadata,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
    }



@router.delete("/github")
def github_disconnect(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Disconnect GitHub account."""
    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github"
    ).first()

    if account:
        session.delete(account)
        session.commit()

    return {"status": "disconnected"}


# ─── GitHub Sync (Repo Analysis) ─────────────────────────────────

GITHUB_REPOS_URL = "https://api.github.com/user/repos"


class RepoAnalysis(BaseModel):
    name: str
    full_name: str
    description: str | None
    language: str | None
    languages: dict[str, int]  # {"Python": 12345, "JavaScript": 678}
    stars: int
    commits_count: int
    last_push: str | None
    url: str


@router.post("/github/sync")
def github_sync(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Sync GitHub repos and extract skill evidence."""
    from ..core.evidence.github_analyzer import GitHubAnalyzer
    from ..core.evidence.github_evidence import create_github_evidence

    # Get connected account
    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github"
    ).first()

    if not account:
        raise HTTPException(status_code=400, detail="GitHub not connected")

    # Decrypt token
    access_token = token_encryption.decrypt(account.access_token)

    # Analyze repos
    analyzer = GitHubAnalyzer(access_token)
    repos = analyzer.get_top_repos(limit=20)

    # Create evidence items
    stats = create_github_evidence(
        user_id=user_id,
        repos=repos,
        source_id=f"github:{account.provider_username}",
        session=session
    )

    # Update last_synced_at
    account.last_synced_at = datetime.utcnow()
    session.commit()

    return {
        "status": "synced",
        "repos_analyzed": len(repos),
        "skills_created": stats["skills_created"],
        "projects_created": stats["projects_created"],
    }

