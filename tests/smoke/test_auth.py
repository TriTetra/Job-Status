"""Authentication guards — no database or Clerk network calls.

The DB session dependency is overridden with a stub, so any request that gets
past auth would fail loudly instead of touching a real database.
"""

import re

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from apps.api.app.dependencies import get_db_session, get_user_id
from shared.config import get_settings

E2E_BYPASS_ENV = "CAREEROS_E2E_AUTH_BYPASS"

# Deliberately unauthenticated (see apps/api/app/main.py)
PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("POST", "/api/webhooks/clerk"),             # Svix signature instead
    ("GET", "/api/oauth/github/callback"),       # single-use OAuth state instead
}


@pytest.fixture(autouse=True)
def _fresh_settings():
    """Settings are cached per process; tests below change env vars."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="module")
def app():
    from apps.api.app.main import app as fastapi_app

    def _no_db():
        raise AssertionError("request reached the database without authentication")
        yield  # pragma: no cover

    fastapi_app.dependency_overrides[get_db_session] = _no_db
    yield fastapi_app
    fastapi_app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _protected_routes(app):
    for path, ops in app.openapi()["paths"].items():
        for method in ops:
            if (method.upper(), path) not in PUBLIC_ROUTES:
                yield method.upper(), path


def _request(headers=None, cookies=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    if cookies:
        raw.append((b"cookie", "; ".join(f"{k}={v}" for k, v in cookies.items()).encode()))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw})


@pytest.fixture
def sandboxed(monkeypatch):
    """If a route leaks past auth, fail fast instead of doing real work:
    no outbound sockets (DB, GitHub, OpenRouter, HN) and no background tasks."""
    import socket

    from fastapi import BackgroundTasks

    real_connect = socket.socket.connect

    def _loopback_only(sock, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):  # asyncio needs loopback socketpairs
            raise ConnectionRefusedError(f"network disabled in auth smoke test: {host}")
        return real_connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", _loopback_only)
    monkeypatch.setattr(BackgroundTasks, "add_task", lambda self, *a, **k: None)


# ── route level ───────────────────────────────────────────────────────────

def test_every_non_public_route_rejects_anonymous_requests(app, client, sandboxed):
    leaks = []
    for method, path in _protected_routes(app):
        url = re.sub(r"\{[^}]+\}", "x", path)
        try:
            status = client.request(method, url).status_code
        except Exception as e:  # handler ran past auth and blew up on the sandbox
            status = f"{type(e).__name__}: {e}"
        if status != 401:
            leaks.append(f"{method} {path} -> {status}")
    assert not leaks, "routes reachable without auth:\n" + "\n".join(leaks)


def test_public_routes_still_public(client):
    assert client.get("/health").status_code == 200


@pytest.fixture
def webhook_client(app, client):
    """The webhook resolves a DB session before verifying; give it an inert one."""
    def _inert_session():
        yield None

    previous = app.dependency_overrides[get_db_session]
    app.dependency_overrides[get_db_session] = _inert_session
    yield client
    app.dependency_overrides[get_db_session] = previous


def test_webhook_rejected_when_secret_missing(webhook_client, monkeypatch):
    monkeypatch.delenv("CLERK_WEBHOOK_SECRET", raising=False)
    assert webhook_client.post("/api/webhooks/clerk", content=b"{}").status_code == 503


def test_webhook_rejects_bad_signature(webhook_client, monkeypatch):
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET", "whsec_dGVzdHNlY3JldA==")
    resp = webhook_client.post(
        "/api/webhooks/clerk",
        content=b"{}",
        headers={"svix-id": "msg_1", "svix-timestamp": "0", "svix-signature": "v1,bogus"},
    )
    assert resp.status_code == 401


# ── get_user_id ───────────────────────────────────────────────────────────

def test_anonymous_request_is_rejected():
    with pytest.raises(HTTPException) as exc:
        get_user_id(_request(), x_user_id=None)
    assert exc.value.status_code == 401


def test_forged_user_id_header_is_rejected():
    with pytest.raises(HTTPException) as exc:
        get_user_id(_request(), x_user_id="user_someone_else")
    assert exc.value.status_code == 401


def test_e2e_header_rejected_without_opt_in(monkeypatch):
    monkeypatch.delenv(E2E_BYPASS_ENV, raising=False)
    with pytest.raises(HTTPException) as exc:
        get_user_id(_request(), x_user_id="user_e2e_attacker")
    assert exc.value.status_code == 401


def test_e2e_header_accepted_with_opt_in(monkeypatch):
    monkeypatch.setenv(E2E_BYPASS_ENV, "1")
    assert get_user_id(_request(), x_user_id="user_e2e_abc") == "user_e2e_abc"


def test_invalid_bearer_token_is_rejected(monkeypatch):
    from apps.api.app.core.auth.clerk_auth import ClerkAuthenticator

    def _boom(token):
        raise ValueError("bad token")

    monkeypatch.setattr(ClerkAuthenticator, "verify_token", staticmethod(_boom))
    with pytest.raises(HTTPException) as exc:
        get_user_id(_request({"Authorization": "Bearer nope"}), x_user_id=None)
    assert exc.value.status_code == 401


def test_valid_cookie_resolves_user(monkeypatch):
    from apps.api.app.core.auth.clerk_auth import ClerkAuthenticator

    monkeypatch.setattr(ClerkAuthenticator, "verify_token", staticmethod(lambda t: "user_123"))
    assert get_user_id(_request(cookies={"__session": "tok"}), x_user_id=None) == "user_123"


def test_bearer_takes_precedence_over_e2e_header(monkeypatch):
    from apps.api.app.core.auth.clerk_auth import ClerkAuthenticator

    monkeypatch.setenv(E2E_BYPASS_ENV, "1")
    monkeypatch.setattr(ClerkAuthenticator, "verify_token", staticmethod(lambda t: "user_real"))
    req = _request({"Authorization": "Bearer tok"})
    assert get_user_id(req, x_user_id="user_e2e_abc") == "user_real"
