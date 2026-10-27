"""API wiring checks — import the app without touching the database.

The route inventory is a refactor guard: moving code between modules must not
silently drop or rename an endpoint. If a route is added/removed on purpose,
update EXPECTED_PATHS in the same commit.
"""

import inspect

import pytest
from starlette.requests import Request

EXPECTED_PATHS = {
    "/", "/health",
    "/api/applications/", "/api/applications/summary", "/api/applications/{url}",
    "/api/companies/", "/api/companies/hiring", "/api/companies/track",
    "/api/companies/{name}", "/api/companies/{name}/memory",
    "/api/evidence/", "/api/evidence/items", "/api/evidence/items/{item_id}",
    "/api/evidence/portfolio", "/api/evidence/portfolio/crawl", "/api/evidence/portfolio/status",
    "/api/evidence/skills/aggregated", "/api/evidence/sources", "/api/evidence/summary",
    "/api/evidence/{skill}",
    "/api/goals/catalog",
    "/api/jobs/", "/api/jobs/pipeline", "/api/jobs/reasoning/{url}", "/api/jobs/scan",
    "/api/jobs/scan/{job_id}/status", "/api/jobs/{url}",
    "/api/market/refresh", "/api/market/refresh/{job_id}/status", "/api/market/signals",
    "/api/market/summary", "/api/market/trend/{skill}",
    "/api/oauth/github", "/api/oauth/github/authorize", "/api/oauth/github/callback",
    "/api/oauth/github/status", "/api/oauth/github/sync",
    "/api/onboarding/advance", "/api/onboarding/build-graph",
    "/api/onboarding/build-graph/{job_id}/status", "/api/onboarding/career-graph",
    "/api/onboarding/complete", "/api/onboarding/goals", "/api/onboarding/identity",
    "/api/onboarding/resume", "/api/onboarding/resume/{job_id}/status", "/api/onboarding/state",
    "/api/preferences",
    "/api/resume/generate",
    "/api/roles", "/api/roles/categories", "/api/roles/search", "/api/roles/{slug}",
    "/api/settings/", "/api/settings/weights",
    "/api/webhooks/clerk",
}


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


def test_route_inventory_unchanged(app):
    assert set(app.openapi()["paths"]) == EXPECTED_PATHS


@pytest.mark.xfail(strict=True, reason="known bug: jobs router passes job_dicts=, run_pipeline expects job_meta=")
def test_scan_router_calls_run_pipeline_with_valid_kwargs():
    from services.job_intelligence.application.scoring_service import ScoringService

    params = inspect.signature(ScoringService.run_pipeline).parameters
    assert "job_dicts" in params


def _anonymous_request(headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw})


@pytest.mark.xfail(strict=True, reason="known security bug: no credentials falls back to user 'default'")
def test_anonymous_request_is_rejected():
    from fastapi import HTTPException

    from app.dependencies import get_user_id

    with pytest.raises(HTTPException) as exc:
        get_user_id(_anonymous_request(), x_user_id=None)
    assert exc.value.status_code == 401


@pytest.mark.xfail(strict=True, reason="known security bug: X-User-Id e2e bypass is active in every environment")
def test_e2e_header_bypass_is_rejected_outside_test_env():
    from fastapi import HTTPException

    from app.dependencies import get_user_id

    with pytest.raises(HTTPException):
        get_user_id(_anonymous_request({"X-User-Id": "user_e2e_attacker"}), x_user_id="user_e2e_attacker")


def test_forged_non_e2e_user_id_is_rejected():
    from fastapi import HTTPException

    from app.dependencies import get_user_id

    with pytest.raises(HTTPException) as exc:
        get_user_id(_anonymous_request(), x_user_id="user_someone_else")
    assert exc.value.status_code == 401
