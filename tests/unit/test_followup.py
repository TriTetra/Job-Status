"""Follow-ups (careeros/applications/followup.py): due at 14 and 21 days, once each, never after an answer
or "don't follow up"; drafts state nothing the evidence doesn't support."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import careeros.db.models  # noqa: F401
from careeros.applications import followup
from careeros.applications.models.email import Email

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)
URL = "https://acme.ai/jobs/1"


def _app(days_ago: float, status: str = "applied"):
    return SimpleNamespace(url=URL, title="ML Engineer", company="Acme", status=status,
                           applied_at=NOW - timedelta(days=days_ago), history=[], updated_at=NOW)


def _mail(kind: str, sent_days_ago=None, id=1):
    return SimpleNamespace(id=id, url=URL, template_type=kind, sequence_num=1 if kind.endswith("1") else 2,
                           sent_at=(NOW - timedelta(days=sent_days_ago)) if sent_days_ago is not None else None)


def test_when_a_follow_up_is_due():
    assert followup.state(_app(10), [], NOW)["due"] is None                    # too early
    assert followup.state(_app(14), [], NOW)["due"] == 1
    assert followup.state(_app(16), [_mail("follow_up_1", 2)], NOW)["due"] is None   # just followed up
    assert followup.state(_app(21), [_mail("follow_up_1", 7)], NOW)["due"] == 2      # the last check-in
    assert followup.state(_app(21), [_mail("follow_up_1", 3)], NOW)["due"] is None   # a week between them
    done = [_mail("follow_up_1", 20), _mail("follow_up_2", 10, id=2)]
    assert followup.state(_app(40), done, NOW)["due"] is None                  # never a third time
    assert followup.state(_app(30), [_mail("follow_up_skipped")], NOW)["due"] is None  # "don't follow up"
    assert followup.state(_app(30, "interview"), [], NOW)["due"] is None       # they answered
    st = followup.state(_app(15), [_mail("follow_up_1", None, id=9)], NOW)
    assert st["due"] == 1 and st["draft_id"] == 9 and st["days_waiting"] == 15  # an unsent draft is reused


def test_template_states_nothing_unsupported():
    ctx = {"title": "ML Engineer", "company": "Acme", "matched": ["PyTorch", "Python", "Docker"]}
    one = followup.template(ctx, 1, "November 9", "Abdullokh")
    assert one.subject == "Following up on my ML Engineer application"
    assert "November 9" in one.body and "PyTorch and Python" in one.body and one.body.endswith("Abdullokh")
    two = followup.template({"title": "ML Engineer"}, 2, "November 2", None)
    assert two.subject.startswith("Checking in") and "experience with" not in two.body


def test_trim_keeps_paragraphs():
    text = "Hello,\n\n" + " ".join(["word"] * 200) + "\n\nBest regards,\nA"
    out = followup._trim(text, 50)
    assert out.startswith("Hello,\n\n") and len(out.split()) <= 63


class _Q:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *a, **k):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class _Session:
    def __init__(self, app, emails):
        self.app, self.emails, self.added = app, emails, []

    def query(self, model):
        return _Q([self.app] if model is not Email else self.emails)

    def add(self, row):
        if row not in self.emails:
            row.id = 100 + len(self.added)
            self.emails.append(row)
            self.added.append(row)

    def flush(self):
        pass

    def get(self, model, key):
        return next((e for e in self.emails if e.id == key), None)


def test_draft_is_written_once_and_marked_sent(monkeypatch):
    calls = []
    monkeypatch.setattr(followup, "write", lambda s, u, a, step, now: calls.append(step) or (
        followup.FollowUp(subject="Following up", body="Hello,\n\nStill keen.\n\nBest regards,"), [], "llm"))
    events = []
    import careeros.memory.events as ev
    monkeypatch.setattr(ev, "remember", lambda *a, **k: events.append((a[2], a[3])))

    s = _Session(_app(15), [])
    d = followup.draft(s, "u1", URL, now=NOW)
    assert d["step"] == 1 and d["subject"] == "Following up" and calls == [1]
    again = followup.draft(s, "u1", URL, now=NOW)
    assert again["id"] == d["id"] and calls == [1]                   # kept, not rewritten
    followup.draft(s, "u1", URL, refresh=True, now=NOW)
    assert calls == [1, 1] and len(s.added) == 1                      # rewritten in place

    sent = followup.mark_sent(s, "u1", d["id"], now=NOW)
    assert sent["sent_at"] and events == [("FollowUpSent", {"url": URL, "step": 1})]
    with pytest.raises(ValueError):                                   # nothing due right after sending
        followup.draft(s, "u1", URL, now=NOW + timedelta(days=1))
    with pytest.raises(LookupError):
        followup.mark_sent(s, "someone-else", d["id"], now=NOW)


def test_skip_stops_the_suggestions():
    s = _Session(_app(20), [])
    followup.skip(s, "u1", URL, now=NOW)
    followup.skip(s, "u1", URL, now=NOW)
    assert [e.template_type for e in s.emails] == ["follow_up_skipped"]
    with pytest.raises(ValueError):
        followup.draft(s, "u1", URL, now=NOW)
