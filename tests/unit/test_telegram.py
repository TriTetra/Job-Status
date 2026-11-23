"""Telegram notifications: connecting by /start token, /stop, the messages, sending each job once."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import careeros.db.models  # noqa: F401  (every model registered, as in the app)

from careeros.notifications import links, notify, telegram
from careeros.notifications.models import TelegramLink


class FakeSession:
    def __init__(self, rows=()):
        self.rows = {r.user_id: r for r in rows}
        self.commits = 0

    def get(self, model, key):
        return self.rows.get(key)

    def add(self, row):
        self.rows[row.user_id] = row

    def flush(self):
        pass

    def commit(self):
        self.commits += 1


@pytest.fixture
def sent(monkeypatch):
    out = []
    monkeypatch.setattr(telegram, "available", lambda: True)
    monkeypatch.setattr(telegram, "send", lambda chat_id, text: out.append((chat_id, text)))
    return out


def _update(text, chat_id=555, chat_type="private"):
    return {"message": {"chat": {"id": chat_id, "type": chat_type}, "text": text, "from": {"username": "ada"}}}


def test_start_with_a_valid_token_connects_and_premarks_existing_matches(monkeypatch, sent):
    row = TelegramLink(user_id="u1", prefs={}, sent=[], link_token_hash=links._hash("tok"),
                       link_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    other = TelegramLink(user_id="u2", chat_id=555, username="old", prefs={}, sent=[])
    s = FakeSession([row, other])
    monkeypatch.setattr(links, "_row_for_token", lambda sess, t: row if t == "tok" else None)
    monkeypatch.setattr(links, "_rows_for_chat", lambda sess, c, exclude_user=None:
                        [r for r in s.rows.values() if r.chat_id == c and r.user_id != exclude_user])
    monkeypatch.setattr(links, "_already_known", lambda sess, uid: ["https://jobs/1", "remind:https://jobs/2"])

    reply = links.handle_update(s, _update("/start tok"))

    assert row.chat_id == 555 and row.username == "ada" and row.link_token_hash is None
    assert other.chat_id is None                                    # one chat, one account
    assert row.sent == ["https://jobs/1", "remind:https://jobs/2"]  # old matches aren't re-sent
    assert "Connected" in reply and sent[-1][0] == 555


def test_expired_token_stop_and_group_chats(monkeypatch, sent):
    s = FakeSession([TelegramLink(user_id="u1", chat_id=555, prefs={}, sent=[])])
    monkeypatch.setattr(links, "_row_for_token", lambda sess, t: None)
    monkeypatch.setattr(links, "_rows_for_chat", lambda sess, c, exclude_user=None:
                        [r for r in s.rows.values() if r.chat_id == c])
    assert "expired" in links.handle_update(s, _update("/start nope"))
    assert links.handle_update(s, _update("/start tok", chat_type="group")) is None
    assert "Disconnected" in links.handle_update(s, _update("/stop"))
    assert s.rows["u1"].chat_id is None
    assert "Settings" in links.handle_update(s, _update("hello"))


def test_webhook_secret_check(monkeypatch):
    monkeypatch.setattr(telegram, "_token", lambda: "123:abc")
    good = telegram.webhook_secret()
    assert telegram.secret_ok(good) and not telegram.secret_ok("x") and not telegram.secret_ok(None)
    monkeypatch.setattr(telegram, "_token", lambda: None)
    assert not telegram.secret_ok(good)


def test_messages_escape_html_and_link_into_aplio(monkeypatch):
    monkeypatch.setattr(notify, "get_settings", lambda: SimpleNamespace(web_app_url="https://career.example"))
    text = notify.matches_message([{"url": "https://jobs.x/a?b=1", "title": "ML <Engineer>", "company": "A&B",
                                    "score": 72, "where": "Remote"}])
    assert "ML &lt;Engineer&gt;" in text and "A&amp;B" in text
    assert "https://career.example/inbox?job=https%3A%2F%2Fjobs.x%2Fa%3Fb%3D1" in text
    assert text.startswith("🎯 <b>1 new strong match</b>")


def test_notify_sends_only_whats_new_once(monkeypatch, sent):
    row = TelegramLink(user_id="u1", chat_id=555, prefs={"matches": True, "reminders": True, "report": False},
                       sent=["https://jobs/old"])
    s = FakeSession([row])
    monkeypatch.setattr(notify, "get_settings", lambda: SimpleNamespace(web_app_url="https://career.example"))
    monkeypatch.setattr(notify, "strong_matches", lambda sess, uid, limit=50: [
        {"url": "https://jobs/old", "title": "Old", "company": "X", "score": 70, "where": ""},
        {"url": "https://jobs/new", "title": "New", "company": "Y", "score": 68, "where": "Berlin"}])
    import careeros.applications.followup as followup_mod
    waiting = [{"url": "https://jobs/app", "title": "Waiting", "company": "Z", "due": 1, "days_waiting": 16}]
    monkeypatch.setattr(followup_mod, "due", lambda sess, uid, now=None: waiting)

    assert notify.notify_user(s, "u1") == 2
    assert "New" in sent[0][1] and "Old" not in sent[0][1]
    assert "Waiting" in sent[1][1] and "follow-up draft" in sent[1][1]
    assert "/applications?open=https%3A%2F%2Fjobs%2Fapp" in sent[1][1]   # opens the draft
    assert notify.notify_user(s, "u1") == 0                     # nothing new the second time
    waiting[0] = {**waiting[0], "due": 2, "days_waiting": 22}       # the last check-in is a new reminder
    assert notify.notify_user(s, "u1") == 1 and "last check-in draft" in sent[-1][1]
    assert notify.notify_user(s, "u1") == 0
    row.prefs = {"matches": False, "reminders": False, "report": False}
    assert notify.notify_user(s, "u1") == 0


def test_daily_report_goes_out_once_a_day(monkeypatch, sent):
    from datetime import datetime, timezone

    import careeros.applications.report as report_mod

    row = TelegramLink(user_id="u1", chat_id=555, prefs={"matches": False, "reminders": False, "report": True}, sent=[])
    s = FakeSession([row])
    monkeypatch.setattr(notify, "get_settings", lambda: SimpleNamespace(web_app_url="https://career.example"))
    monkeypatch.setattr(report_mod, "daily_report", lambda sess, uid, now=None: {
        "date": "2026-11-23", "sent_this_week": 1, "active": [], "learn": [], "new_good_matches": 0,
        "queue": [{"title": "AI Engineer", "company": "Clera", "score": 89}]})
    day = datetime(2026, 11, 23, 9, tzinfo=timezone.utc)
    assert notify.notify_user(s, "u1", day) == 1
    assert "1 ready to apply" in sent[-1][1] and "/apply" in sent[-1][1]
    assert notify.notify_user(s, "u1", day) == 0                 # same day: not again
    assert notify.notify_user(s, "u1", datetime(2026, 11, 24, 9, tzinfo=timezone.utc)) == 1
