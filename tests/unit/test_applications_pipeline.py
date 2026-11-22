"""Applications: stages reached from history, the analytics numbers, and history being written."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from careeros.applications import pipeline
from careeros.applications.repositories.application_repo import ApplicationRepository

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


def _at(days: float) -> str:
    return (NOW - timedelta(days=days)).isoformat()


def _app(url, status, history, applied_days=None):
    return SimpleNamespace(url=url, status=status, history=history, notes=None, title=url, company=None,
                           applied_at=NOW - timedelta(days=applied_days) if applied_days is not None else None,
                           created_at=NOW - timedelta(days=40), updated_at=NOW - timedelta(days=1))


def test_reached_counts_a_rejection_after_an_interview_as_an_interview():
    app = _app("a", "rejected", [{"status": "to_apply", "at": _at(30)}, {"status": "applied", "at": _at(25)},
                                 {"status": "interview", "at": _at(15)}, {"status": "rejected", "at": _at(5)}])
    assert {"applied", "interview", "rejected"} <= pipeline.reached(app)
    assert "offer" not in pipeline.reached(app)


def test_offer_implies_applied_and_interview_even_without_history():
    assert {"applied", "interview", "offer"} <= pipeline.reached(_app("a", "offer", []))


def test_analytics_funnel_response_and_bands(monkeypatch):
    apps = [
        _app("strong-int", "interview", [{"status": "applied", "at": _at(20)}, {"status": "interview", "at": _at(6)}], 20),
        _app("weak-rej", "rejected", [{"status": "applied", "at": _at(30)}, {"status": "rejected", "at": _at(10)}], 30),
        _app("waiting", "applied", [{"status": "applied", "at": _at(16)}], 16),
        _app("new", "applied", [{"status": "applied", "at": _at(2)}], 2),
        _app("queued", "to_apply", [{"status": "to_apply", "at": _at(3)}]),
        _app("passed", "skipped", [{"status": "skipped", "at": _at(1)}]),
    ]
    scores = {"strong-int": SimpleNamespace(career_score=78), "weak-rej": SimpleNamespace(career_score=50),
              "waiting": SimpleNamespace(career_score=72)}
    monkeypatch.setattr(pipeline, "_apps", lambda s, u: apps)
    def fake_scores(s, u, urls):
        wanted = set(urls)
        return {k: v for k, v in scores.items() if k in wanted}

    monkeypatch.setattr(pipeline, "_scores", fake_scores)
    monkeypatch.setattr(pipeline, "_open_matches", lambda s, u: 9)

    a = pipeline.analytics(None, "u", now=NOW)

    assert [f["count"] for f in a["funnel"]] == [5, 4, 1, 0]          # skipped is not tracked
    assert a["interview_rate"] == 0.25
    assert a["weekly_applied"][-1] == 1 and sum(a["weekly_applied"]) == 4
    assert a["response"] == {"rate": 0.67, "answered": 2, "sent": 3}  # sent 2+ weeks ago: 3, heard back: 2
    assert a["waiting"] == {"count": 2, "median_days": 9, "stale": 1}
    assert a["by_score"][0] == {"band": "70+", "applied": 2, "interviews": 1}
    assert a["by_score"][2] == {"band": "Under 55", "applied": 1, "interviews": 0}
    assert a["passed_on"] == 1 and a["open_matches"] == 9


class _Session:
    def flush(self):
        pass

    def add(self, obj):
        pass


def test_moving_logs_history_and_stamps_applied_at_once():
    repo = ApplicationRepository(_Session())
    app = SimpleNamespace(status="to_apply", history=[{"status": "to_apply", "at": _at(5)}], applied_at=None, notes=None)
    repo._move(app, "applied")
    first_applied = app.applied_at
    assert app.status == "applied" and first_applied is not None
    repo._move(app, "interview")
    assert app.applied_at == first_applied
    assert [e["status"] for e in app.history] == ["to_apply", "applied", "interview"]
    repo._move(app, "interview")  # no-op: same status
    assert len(app.history) == 3
