"""Board-driven companies and the own-corpus market: trend rule, skill reading."""

from types import SimpleNamespace

import pytest

from careeros.companies.directory import hiring_trend, job_skills


@pytest.mark.parametrize("this_week, last_week, expected", [
    (12, 3, "spike"),     # five or more, at least double
    (5, 0, "spike"),
    (4, 3, "up"),         # 3+ and a quarter more
    (3, 3, "stable"),
    (1, 0, "stable"),     # one new posting isn't a trend
    (2, 6, "down"),       # under 60% of a real week
    (0, 2, "stable"),     # too small to call
])
def test_hiring_trend(this_week, last_week, expected):
    assert hiring_trend(this_week, last_week) == expected


def _job(**kw):
    base = dict(llm_facts=None, llm_facts_hash=None, content_hash="h1", required_skills=[])
    return SimpleNamespace(**{**base, **kw})


def test_job_skills_prefer_current_llm_facts_and_canonicalise():
    job = _job(llm_facts={"required_skills": ["golang", "Postgres", "go"]}, llm_facts_hash="h1",
               required_skills=["Java"])
    assert job_skills(job) == ["Go", "PostgreSQL"]


def test_job_skills_fall_back_to_keywords_when_facts_are_stale():
    job = _job(llm_facts={"required_skills": ["Rust"]}, llm_facts_hash="old", required_skills=["python", "", None])
    assert job_skills(job) == ["Python"]
