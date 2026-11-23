"""Person memory log (careeros/memory): event rules, payloads, streams, skip reasons, CV refs."""

import re
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from careeros.memory import events as ev
from careeros.memory.cv import cv_ref


def test_job_stream_is_short_stable_and_distinct():
    a, b = ev.job_stream("https://x.test/jobs/1"), ev.job_stream("https://x.test/jobs/2")
    assert a == ev.job_stream("https://x.test/jobs/1") and a != b
    assert a.startswith("job:") and len(a) == 20


def test_payload_is_json_safe_and_small():
    when = datetime(2026, 11, 23, tzinfo=timezone.utc)
    assert ev.clean_payload({"at": when, "n": 1}) == {"at": when.isoformat(), "n": 1}
    assert ev.clean_payload(None) == {}
    with pytest.raises(ValueError):
        ev.clean_payload({"text": "x" * (ev.MAX_PAYLOAD_BYTES + 1)})  # a document, not a reference


def test_actors_separate_the_person_from_inferences():
    assert ev.valid_actor("user") and ev.valid_actor("agent:matcher") and ev.valid_actor("import:github")
    assert not ev.valid_actor("admin") and not ev.valid_actor("")


def test_record_refuses_unknown_types_and_actors_before_touching_the_database():
    untouched = SimpleNamespace()  # any database call would fail on this
    with pytest.raises(ValueError):
        ev.record(untouched, "u", "SomethingHappened")
    with pytest.raises(ValueError):
        ev.record(untouched, "u", "JobSkipped", actor="robot")


def test_remember_never_raises():
    class Broken:
        def begin_nested(self):
            raise RuntimeError("database down")

    assert ev.remember(Broken(), "u", "JobSkipped", {"url": "x"}) is None


def test_skip_reasons_match_the_web_app():
    web = Path(__file__).parents[2] / "apps" / "web" / "features" / "opportunities" / "format.ts"
    ids = set(re.findall(r'\{ id: "([a-z_]+)", label:', web.read_text(encoding="utf-8")))
    assert ids == set(ev.SKIP_REASONS)


def test_cv_reference():
    assert cv_ref(12, 3) == "doc:12@v3"


def test_application_moves_become_events(monkeypatch):
    from careeros.applications.repositories import application_repo as repo_mod

    seen = []
    monkeypatch.setattr("careeros.memory.events.remember", lambda s, u, t, p=None, **kw: seen.append((t, p, kw)))
    repo = repo_mod.ApplicationRepository(SimpleNamespace())
    monkeypatch.setattr(repo, "update", lambda obj, **kw: (obj.__dict__.update(kw), obj)[1])
    monkeypatch.setattr(repo, "_cv", lambda u: {"document_id": 4, "version": 2, "filename": "cv.pdf", "ref": "doc:4@v2"})
    app = SimpleNamespace(user_id="u1", url="https://x.test/j", title="ML Engineer", company="Acme", status="to_apply",
                          history=[], applied_at=None, notes=None, resume_version=None)
    repo._move(app, "applied")
    assert app.resume_version == "doc:4@v2"                       # the CV that was sent
    assert seen[-1][0] == "ApplicationStageChanged" and seen[-1][1]["cv"]["ref"] == "doc:4@v2"
    repo._move(app, "interview")
    assert seen[-1][0] == "OutcomeObserved" and seen[-1][1]["kind"] == "interview"
    assert seen[-1][2]["stream"] == ev.job_stream("https://x.test/j")
