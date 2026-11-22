"""Briefing v2: visit windows, dismissed to-dos, chance bands."""

from datetime import datetime, timedelta, timezone

import careeros.db.models  # noqa: F401 — every model registered (User → Application → Email)
from careeros.briefing import digest
from careeros.identity.models.user import User

T0 = datetime(2026, 11, 22, 8, 0, tzinfo=timezone.utc)


def _user(profile=None):
    return User(id="u1", email="a@b.c", profile_data=profile or {})


def test_first_visit_looks_back_a_day_and_remembers_it():
    u = _user()
    since, hours = digest.record_visit(u, T0)
    assert since == T0 - timedelta(hours=24) and hours is None
    assert u.profile_data["briefing_seen"]["at"] == T0.isoformat()


def test_next_day_visit_starts_from_the_last_one():
    u = _user()
    digest.record_visit(u, T0)
    later = T0 + timedelta(hours=26)
    since, hours = digest.record_visit(u, later)
    assert since == T0 and hours == 26
    assert u.profile_data["briefing_seen"] == {"at": later.isoformat(), "prev": T0.isoformat()}


def test_reload_within_a_visit_keeps_the_same_window():
    u = _user()
    digest.record_visit(u, T0)
    later = T0 + timedelta(hours=26)
    digest.record_visit(u, later)
    since, hours = digest.record_visit(u, later + timedelta(minutes=5))  # e.g. the time-zone refresh
    assert since == T0 and round(hours) == 26


def test_dismissed_todos_expire_after_a_week():
    class Q:
        def __init__(self, user):
            self.user = user

        def filter(self, *a):
            return self

        def first(self):
            return self.user

    u = _user({"briefing_dismissed": {"old": (T0 - timedelta(days=8)).isoformat()}})
    session = type("S", (), {"query": lambda self, model: Q(u)})()
    digest.dismiss(session, "u1", "gap:kafka", now=T0)
    assert set(u.profile_data["briefing_dismissed"]) == {"gap:kafka"}  # the 8-day-old one dropped


def test_chance_bands():
    assert [digest._chance(v) for v in (None, 10, 15, 29.9, 30, 80)] == ["low", "low", "medium", "medium", "high", "high"]
