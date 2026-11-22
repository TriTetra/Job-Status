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


def test_weekly_new_buckets_oldest_first():
    from datetime import datetime, timedelta, timezone

    from careeros.companies.directory import weekly_new

    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    dates = [now - timedelta(days=1), now - timedelta(days=3), now - timedelta(days=9), now - timedelta(days=50), None]

    class Q:
        def filter(self, *a):
            return self

        def all(self):
            return [(d,) for d in dates]

    session = SimpleNamespace(query=lambda *a: Q())
    assert weekly_new(session, "x", now) == [1, 0, 0, 0, 0, 0, 1, 2]  # 50 days ago is week 8 of 8
