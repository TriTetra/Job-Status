"""Linking a user's GitHub account (OAuth) and syncing it into evidence.

Flow: authorize_url() → GitHub → complete_authorization(state, code) → token
encrypted at rest in connected_accounts → sync_evidence() on demand.
"""

import logging
import secrets
import threading
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests
from sqlalchemy.orm import Session

from careeros.identity.models.connected_account import ConnectedAccount
from careeros.shared.config import get_settings
from careeros.shared.crypto import get_token_cipher

logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"
# `repo` lets evidence include private repos the user owns
SCOPES = "read:user user:email repo"
STATE_TTL = timedelta(minutes=10)
SYNC_REPO_LIMIT = 20


class GitHubAccountError(Exception):
    """Failure with a message safe to show the user (details go to the log)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class OAuthStates:
    """Single-use CSRF state tokens, in process memory (lost on restart; one worker only)."""

    def __init__(self, ttl: timedelta = STATE_TTL) -> None:
        self._states: dict[str, tuple[str, datetime]] = {}
        self._lock = threading.Lock()
        self._ttl = ttl

    def issue(self, user_id: str) -> str:
        state = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        with self._lock:
            self._states = {s: v for s, v in self._states.items() if now - v[1] < self._ttl}
            self._states[state] = (user_id, now)
        return state

    def consume(self, state: str) -> Optional[str]:
        """The user id the state was issued to, or None if unknown/expired. A state works once."""
        with self._lock:
            entry = self._states.pop(state, None)
        if entry is None or datetime.utcnow() - entry[1] >= self._ttl:
            return None
        return entry[0]


oauth_states = OAuthStates()


def _account(session: Session, user_id: str) -> Optional[ConnectedAccount]:
    return session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github",
    ).first()


def authorize_url(user_id: str) -> str:
    s = get_settings()
    if not s.github_client_id or not s.github_redirect_uri:
        raise GitHubAccountError("GitHub OAuth not configured", 500)
    params = {
        "client_id": s.github_client_id,
        "redirect_uri": s.github_redirect_uri,
        "scope": SCOPES,
        "state": oauth_states.issue(user_id),
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def _exchange_code(code: str, http) -> str:
    s = get_settings()
    resp = http.post(
        TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": s.github_client_id,
            "client_secret": s.github_client_secret,
            "code": code,
            "redirect_uri": s.github_redirect_uri,
        },
        timeout=10,
    )
    token = resp.json().get("access_token") if resp.status_code == 200 else None
    if not token:
        # GitHub's body can contain error details we should not echo to the browser
        logger.warning("GitHub token exchange failed: HTTP %s %s", resp.status_code, resp.text[:300])
        raise GitHubAccountError("GitHub authorization failed", 502)
    return token


def _fetch_user(token: str, http) -> dict:
    resp = http.get(USER_URL, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=10)
    if resp.status_code != 200:
        logger.warning("GitHub user fetch failed: HTTP %s", resp.status_code)
        raise GitHubAccountError("Failed to fetch GitHub user info", 502)
    return resp.json()


def complete_authorization(session: Session, state: str, code: str, http=requests) -> str:
    """Finish the OAuth callback: verify state, store the encrypted token. Returns the user id."""
    user_id = oauth_states.consume(state)
    if user_id is None:
        raise GitHubAccountError("Invalid or expired state", 400)

    token = _exchange_code(code, http)
    gh_user = _fetch_user(token, http)

    account = _account(session, user_id)
    if account is None:
        account = ConnectedAccount(user_id=user_id, provider="github")
        session.add(account)
    account.provider_user_id = str(gh_user["id"])
    account.provider_username = gh_user["login"]
    account.access_token = get_token_cipher().encrypt(token)
    account.account_metadata = {
        "avatar_url": gh_user.get("avatar_url"),
        "public_repos": gh_user.get("public_repos", 0),
        "followers": gh_user.get("followers", 0),
        "bio": gh_user.get("bio"),
    }
    account.last_synced_at = datetime.utcnow()
    session.commit()
    return user_id


def account_status(session: Session, user_id: str) -> dict:
    account = _account(session, user_id)
    if not account:
        return {"connected": False}
    return {
        "connected": True,
        "username": account.provider_username,
        "provider_user_id": account.provider_user_id,
        "metadata": account.account_metadata,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
    }


def disconnect(session: Session, user_id: str) -> None:
    account = _account(session, user_id)
    if account:
        session.delete(account)
        session.commit()


def sync_evidence(session: Session, user_id: str) -> dict:
    """Re-read the user's repos and replace their GitHub evidence."""
    from careeros.evidence.github import GitHubAnalyzer, create_github_evidence

    account = _account(session, user_id)
    if not account:
        raise GitHubAccountError("GitHub not connected", 400)

    repos = GitHubAnalyzer(get_token_cipher().decrypt(account.access_token)).get_top_repos(limit=SYNC_REPO_LIMIT)
    stats = create_github_evidence(user_id=user_id, repos=repos, session=session)
    account.last_synced_at = datetime.utcnow()
    session.commit()
    return {
        "status": "synced",
        "repos_analyzed": len(repos),
        "skills_created": stats["skills_created"],
        "projects_created": stats["projects_created"],
    }
