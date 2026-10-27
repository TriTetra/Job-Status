"""Authentication + CSRF guards on the real app — no database or network.

The DB session dependency yields a session that explodes on any use, so a
request that gets past auth fails loudly instead of touching a database.
"""

import re

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from apps.api.app import dependencies
from apps.api.app.dependencies import get_db_session, get_user_id
from careeros.identity.auth.sessions import COOKIE_NAME
from careeros.shared.config import get_settings

E2E_BYPASS_ENV = "CAREEROS_E2E_AUTH_BYPASS"
CSRF = {"X-CareerOS-CSRF": "1"}

# Deliberately reachable without a session (see apps/api/app/main.py)
PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("POST", "/api/auth/login"),           # how you get a session
    ("POST", "/api/auth/logout"),          # harmless without one
    ("GET", "/api/oauth/github/callback"),  # single-use OAuth state instead
}


class ExplodingSession:
    def __getattr__(self, name):
        raise AssertionError(f"request reached the database (session.{name}) without authentication")


@pytest.fixture(autouse=True)
def _fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="module")
def app():
    from apps.api.app.main import app as fastapi_app

    def _exploding_db():
        yield ExplodingSession()

    fastapi_app.dependency_overrides[get_db_session] = _exploding_db
    yield fastapi_app
    fastapi_app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app, raise_server_exceptions=False)


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


def _routes(app):
    for path, ops in app.openapi()["paths"].items():
        for method in ops:
            yield method.upper(), path


# ── route level ───────────────────────────────────────────────────────────

def test_every_non_public_route_rejects_requests_without_a_session(app, client, sandboxed):
    leaks = []
    for method, path in _routes(app):
        if (method, path) in PUBLIC_ROUTES:
            continue
        url = re.sub(r"\{[^}]+\}", "x", path)
        try:
            status = client.request(method, url, headers=CSRF).status_code
        except Exception as e:  # handler ran past auth and blew up on the sandbox
            status = f"{type(e).__name__}: {e}"
        if status != 401:
            leaks.append(f"{method} {path} -> {status}")
    assert not leaks, "routes reachable without a session:\n" + "\n".join(leaks)


def test_unsafe_methods_need_the_csrf_header(app, client):
    missing = []
    for method, path in _routes(app):
        if method in ("GET", "HEAD", "OPTIONS"):
            continue
        status = client.request(method, re.sub(r"\{[^}]+\}", "x", path)).status_code
        if status != 403:
            missing.append(f"{method} {path} -> {status}")
    assert not missing, "state-changing routes accepted without CSRF header:\n" + "\n".join(missing)


def test_no_cors_is_granted(client):
    resp = client.options(
        "/api/jobs/",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers}


def test_public_routes_still_public(client):
    assert client.get("/health").status_code == 200


# ── login / logout ────────────────────────────────────────────────────────

@pytest.fixture
def login_env(monkeypatch):
    from types import SimpleNamespace

    from apps.api.app.routers import auth as auth_router
    from careeros.identity.auth.throttle import LoginThrottle

    users = {("me@example.com", "correct horse battery"): SimpleNamespace(id="user_1")}
    monkeypatch.setattr(auth_router.accounts, "authenticate",
                        lambda s, email, pw: users.get((email.lower(), pw)))
    monkeypatch.setattr(auth_router.sessions, "create_session", lambda s, uid, ua, ip: f"token-for-{uid}")
    monkeypatch.setattr(auth_router.sessions, "purge_expired", lambda s: 0)
    monkeypatch.setattr(auth_router.sessions, "revoke_session", lambda s, tok: None)
    monkeypatch.setattr(auth_router, "login_throttle", LoginThrottle(per_email=3, per_ip=10))


def test_login_sets_a_hardened_session_cookie(client, login_env):
    resp = client.post("/api/auth/login", json={"email": "me@example.com", "password": "correct horse battery"},
                       headers=CSRF)
    assert resp.status_code == 204
    cookie = resp.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE_NAME}=token-for-user_1")
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie and "path=/" in cookie


def test_wrong_password_is_401_and_repeated_failures_are_throttled(client, login_env):
    body = {"email": "me@example.com", "password": "nope"}
    assert [client.post("/api/auth/login", json=body, headers=CSRF).status_code for _ in range(3)] == [401] * 3
    blocked = client.post("/api/auth/login", json=body, headers=CSRF)
    assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) > 0
    # even the right password waits out the lock
    ok_body = {"email": "me@example.com", "password": "correct horse battery"}
    assert client.post("/api/auth/login", json=ok_body, headers=CSRF).status_code == 429


def test_login_without_csrf_header_is_refused(client, login_env):
    resp = client.post("/api/auth/login", json={"email": "me@example.com", "password": "correct horse battery"})
    assert resp.status_code == 403


def test_logout_clears_the_cookie(client, login_env):
    resp = client.post("/api/auth/logout", headers=CSRF, cookies={COOKIE_NAME: "whatever"})
    assert resp.status_code == 204
    assert f'{COOKIE_NAME}=""' in resp.headers["set-cookie"] or "max-age=0" in resp.headers["set-cookie"].lower()


# ── get_user_id ───────────────────────────────────────────────────────────

def _request(cookies=None):
    raw = []
    if cookies:
        raw.append((b"cookie", "; ".join(f"{k}={v}" for k, v in cookies.items()).encode()))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw})


def test_valid_session_cookie_resolves_user(monkeypatch):
    monkeypatch.setattr(dependencies, "resolve_session", lambda s, tok: "user_1" if tok == "good" else None)
    assert get_user_id(_request({COOKIE_NAME: "good"}), x_user_id=None, session=object()) == "user_1"


def test_invalid_or_missing_session_is_rejected(monkeypatch):
    monkeypatch.setattr(dependencies, "resolve_session", lambda s, tok: None)
    for req in (_request(), _request({COOKIE_NAME: "forged"})):
        with pytest.raises(HTTPException) as exc:
            get_user_id(req, x_user_id=None, session=object())
        assert exc.value.status_code == 401


def test_forged_user_id_header_is_rejected(monkeypatch):
    monkeypatch.setattr(dependencies, "resolve_session", lambda s, tok: None)
    with pytest.raises(HTTPException):
        get_user_id(_request(), x_user_id="user_someone_else", session=object())


def test_e2e_header_only_with_opt_in(monkeypatch):
    monkeypatch.setattr(dependencies, "resolve_session", lambda s, tok: None)
    monkeypatch.delenv(E2E_BYPASS_ENV, raising=False)
    with pytest.raises(HTTPException):
        get_user_id(_request(), x_user_id="user_e2e_abc", session=object())
    get_settings.cache_clear()
    monkeypatch.setenv(E2E_BYPASS_ENV, "1")
    assert get_user_id(_request(), x_user_id="user_e2e_abc", session=object()) == "user_e2e_abc"


def test_session_beats_e2e_header(monkeypatch):
    monkeypatch.setattr(dependencies, "resolve_session", lambda s, tok: "user_real")
    monkeypatch.setenv(E2E_BYPASS_ENV, "1")
    assert get_user_id(_request({COOKIE_NAME: "good"}), x_user_id="user_e2e_abc", session=object()) == "user_real"
