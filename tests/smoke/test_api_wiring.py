"""API wiring checks — import the app without touching the database.

The route inventory is a refactor guard: moving code between modules must not
silently drop or rename an endpoint. If a route is added/removed on purpose,
update EXPECTED_PATHS in the same commit.
"""

import ast
import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]

EXPECTED_PATHS = {
    "/", "/health",
    "/api/auth/login", "/api/auth/logout", "/api/auth/me",
    "/api/applications/", "/api/applications/summary", "/api/applications/{url}",
    "/api/companies/", "/api/companies/hiring", "/api/companies/track",
    "/api/companies/{name}", "/api/companies/{name}/memory",
    # legacy-table endpoints /api/evidence/, /summary, /{skill} removed in Refactor Step 4
    "/api/evidence/items", "/api/evidence/items/{item_id}",
    "/api/evidence/portfolio", "/api/evidence/portfolio/crawl", "/api/evidence/portfolio/status",
    "/api/evidence/skills/aggregated", "/api/evidence/sources",
    "/api/briefing",
    "/api/goals/catalog",
    "/api/jobs/", "/api/jobs/pipeline", "/api/jobs/reasoning/{url}", "/api/jobs/scan",
    "/api/jobs/scan/{job_id}/status", "/api/jobs/{url}",
    "/api/jobs/boards", "/api/jobs/sync", "/api/jobs/sync/{job_id}/status",
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
}


@pytest.fixture(scope="module")
def app():
    from apps.api.app.main import app as fastapi_app
    return fastapi_app


def test_route_inventory_unchanged(app):
    assert set(app.openapi()["paths"]) == EXPECTED_PATHS


def test_run_pipeline_callers_pass_valid_kwargs():
    """Every ScoringService.run_pipeline(...) call in app code uses keywords it accepts."""
    from careeros.jobs.scoring_service import ScoringService

    accepted = set(inspect.signature(ScoringService.run_pipeline).parameters)
    calls = []
    for d in ("apps", "careeros", "scripts"):
        for path in (ROOT / d).rglob("*.py"):
            if "node_modules" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            calls += [
                (path.relative_to(ROOT).as_posix(), node) for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "run_pipeline"
            ]
    assert any(p.endswith("careeros/jobs/scan.py") for p, _ in calls), "scan no longer calls run_pipeline"
    for path, call in calls:
        passed = {kw.arg for kw in call.keywords if kw.arg}
        assert passed <= accepted, f"{path}:{call.lineno} unexpected kwargs: {passed - accepted}"
