"""ApplyPilot row → canonical Job dict (config from infra/config/plugins.yaml)."""

import pytest

from careeros.shared.config import load_plugin_config
from careeros.jobs.sources.applypilot.adapter import ApplyPilotAdapter


@pytest.fixture(scope="module")
def adapter():
    return ApplyPilotAdapter(load_plugin_config()["job_sources"]["applypilot"])


@pytest.fixture(scope="module")
def cols():
    return load_plugin_config()["job_sources"]["applypilot"]["columns"]


def _row(cols, **values):
    return {cols[k]: v for k, v in values.items()}


def test_normalize_returns_canonical_keys(adapter, cols):
    job = adapter.normalize(_row(cols, url="https://example.com/j/1", title="Backend Engineer", company="Acme"))
    for key in ("url", "title", "company", "location", "remote", "required_skills", "salary_min", "salary_max"):
        assert key in job
    assert job["company"] == "Acme"


def test_company_falls_back_to_ats_slug(adapter, cols):
    job = adapter.normalize(_row(cols, url="https://boards.greenhouse.io/acme-labs/jobs/42", title="Engineer"))
    assert job["company"] == "Acme Labs"


def test_remote_role_gets_region(adapter, cols):
    job = adapter.normalize(_row(
        cols, url="u", title="Engineer", company="Acme",
        location="Remote", full_description="This is a fully remote (Europe) position.",
    ))
    assert job["remote"] is True
    assert job["remote_region"] == "Europe"


def test_missing_values_do_not_crash(adapter):
    job = adapter.normalize({})
    assert job["title"] == "Unknown"
    assert job["location"] == "Unknown"


def test_visa_is_unknown_when_posting_does_not_say(adapter, cols):
    job = adapter.normalize(_row(cols, url="u", title="Engineer", company="Acme", location="Remote"))
    assert job["sponsors_visa"] is None
