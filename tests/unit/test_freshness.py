"""Freshness (careeros/jobs/freshness.py, scheduler ticks): busy cheap boards hourly, costly or quiet
ones less often, failing ones wait; a tick with something new rescores and tells Telegram right away."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import careeros.db.models  # noqa: F401
from careeros.jobs import freshness

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)
H = timedelta(hours=1)


def test_intervals():
    assert freshness.interval("greenhouse", active=True, failed=False) == H
    assert freshness.interval("greenhouse", active=False, failed=False) == 3 * H
    assert freshness.interval("workday", active=True, failed=False) == 3 * H
    assert freshness.interval("smartrecruiters", active=False, failed=False) == 6 * H
    assert freshness.interval("lever", active=True, failed=True) == 6 * H     # a failing board isn't hammered


class _Q:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *a, **k):
        return self

    def group_by(self, *a):
        return self

    def all(self):
        return self.rows


class _Session:
    def __init__(self, runs, recent):
        self.runs, self.recent = runs, recent

    def query(self, *what):
        from careeros.jobs.models.board_run import JobBoardRun

        if what[0] is JobBoardRun:
            return _Q(self.runs)
        return _Q([(k,) for k in self.recent])


def _board(key, ats):
    return SimpleNamespace(key=key, ats=ats)


def _run(key, hours_ago, error=None):
    return SimpleNamespace(company_key=key, last_run_at=NOW - timedelta(hours=hours_ago), last_error=error)


def test_due_boards():
    boards = [_board("busy", "greenhouse"), _board("quiet", "lever"), _board("wd", "workday"),
              _board("broken", "ashby"), _board("new", "ashby")]
    runs = [_run("busy", 0.95), _run("quiet", 2), _run("wd", 3.2), _run("broken", 2, error="HTTP 500")]
    due = freshness.due_boards(_Session(runs, recent={"busy", "wd"}), boards, NOW)
    # busy: hourly (55 min ago is due); quiet: 3 h, read 2 h ago; workday busy: 3 h; broken: waits 6 h; never read: due
    assert due == ["busy", "wd", "new"]


def test_tick_reads_due_boards_then_rescores_and_notifies_only_when_something_is_new(monkeypatch):
    from careeros.applications.mail import sync as mail_sync
    from careeros.jobs import ingest, scan, scheduler
    from careeros.jobs import llm_extract
    from careeros.notifications import notify

    @contextmanager
    def scope():
        yield SimpleNamespace()

    calls = []
    monkeypatch.setattr(scheduler.db, "session_scope", scope)
    monkeypatch.setattr(freshness, "due_boards", lambda s, boards, now=None: ["acme"])
    import careeros.jobs.boards as boards_mod
    monkeypatch.setattr(boards_mod, "all_boards", lambda s=None: [])
    monkeypatch.setattr(scheduler, "refresh_feeds", lambda: 0)
    monkeypatch.setattr(scheduler, "_active_users", lambda: ["u1"])
    monkeypatch.setattr(llm_extract, "enrich_jobs", lambda n: calls.append(("enrich", n)))
    monkeypatch.setattr(scan, "run_scan", lambda job, uid: calls.append(("scan", uid)))
    monkeypatch.setattr(notify, "notify_all", lambda users, report=True: calls.append(("notify", report)))
    monkeypatch.setattr(mail_sync, "check_all", lambda users: calls.append(("mail",)))

    summary = ingest.SyncSummary(boards=[ingest.BoardResult(key="acme", name="Acme", ats="greenhouse", new=2)])
    monkeypatch.setattr(ingest, "sync_all", lambda keys=None: calls.append(("sync", tuple(keys))) or summary)
    marks, due_tasks = [], {"task:mail"}
    monkeypatch.setattr(scheduler, "is_due", lambda task, every, now=None: task in due_tasks)
    monkeypatch.setattr(scheduler, "mark_run", lambda task, now=None: marks.append(task) or due_tasks.discard(task))
    assert scheduler.run_tick() == {"boards": 1, "new": 2}
    assert calls == [("sync", ("acme",)), ("enrich", scheduler.ENRICH_PER_TICK), ("scan", "u1"),
                     ("notify", False), ("mail",)]          # matches now; the daily report waits for its pace
    assert marks == ["task:mail"]                            # when mail was checked is kept in the database

    calls.clear()
    monkeypatch.setattr(ingest, "sync_all", lambda keys=None: calls.append(("sync", tuple(keys))) or ingest.SyncSummary())
    assert scheduler.run_tick() == {"boards": 1, "new": 0}
    assert calls == [("sync", ("acme",))]                    # nothing new: no LLM, no rescore; mail checked an hour ago


def test_run_auto_does_the_full_refresh_only_when_due(monkeypatch):
    from careeros.jobs import scheduler

    monkeypatch.setattr(scheduler, "run_cycle", lambda: {"cycle": True})
    monkeypatch.setattr(scheduler, "run_tick", lambda: {"tick": True})
    monkeypatch.setattr(scheduler, "full_every", lambda: 6 * H)
    monkeypatch.setattr(scheduler, "last_run", lambda task: None)
    assert scheduler.run_auto() == ("cycle", {"cycle": True})                 # never ran: full refresh
    monkeypatch.setattr(scheduler, "last_run", lambda task: datetime.now(timezone.utc) - 2 * H)
    assert scheduler.run_auto() == ("tick", {"tick": True})                   # ran 2 h ago: a tick
    monkeypatch.setattr(scheduler, "last_run", lambda task: datetime.now(timezone.utc) - 7 * H)
    assert scheduler.run_auto()[0] == "cycle"


def test_timers_survive_processes(monkeypatch):
    """When a paced task last ran is read back from the database row it was written to."""
    from careeros.jobs import scheduler
    from careeros.jobs.models.board_run import JobBoardRun

    rows = {}

    class S:
        def get(self, model, key):
            return rows.get(key)

        def execute(self, stmt):
            v = stmt.compile().params
            rows[v["company_key"]] = JobBoardRun(company_key=v["company_key"], last_run_at=v["last_run_at"])

    @contextmanager
    def scope():
        yield S()

    monkeypatch.setattr(scheduler.db, "session_scope", scope)
    assert scheduler.is_due("task:mail", H)                                     # never ran
    scheduler.mark_run("task:mail", NOW)
    assert scheduler.last_run("task:mail") == NOW
    assert not scheduler.is_due("task:mail", H, now=NOW + timedelta(minutes=30))
    assert scheduler.is_due("task:mail", H, now=NOW + timedelta(minutes=61))


def test_worker_commands(monkeypatch):
    from typer.testing import CliRunner

    from careeros.jobs import cli, scheduler

    monkeypatch.setattr(scheduler, "run_auto", lambda: ("tick", {"boards": 2, "new": 0}))
    monkeypatch.setattr(scheduler, "run_tick", lambda: None)
    runner = CliRunner()
    assert "tick: {'boards': 2, 'new': 0}" in runner.invoke(cli.app, ["run"]).output
    assert "skipped, another sync is running" in runner.invoke(cli.app, ["tick"]).output


def test_full_refresh_is_marked_when_it_starts_so_a_failure_is_not_repeated_every_tick(monkeypatch):
    import pytest

    from careeros.applications import queue
    from careeros.applications.mail import sync as mail_sync
    from careeros.jobs import ingest, llm_extract, scheduler
    from careeros.notifications import notify

    marks = []
    monkeypatch.setattr(scheduler, "mark_run", lambda task, now=None: marks.append(task))
    monkeypatch.setattr(scheduler, "refresh_feeds", lambda: 0)
    monkeypatch.setattr(ingest, "sync_all", lambda keys=None: ingest.SyncSummary())
    monkeypatch.setattr(llm_extract, "enrich_jobs", lambda n: None)
    monkeypatch.setattr(scheduler, "_active_users", lambda: [])
    monkeypatch.setattr(mail_sync, "check_all", lambda users: None)
    monkeypatch.setattr(queue, "prepare_all", lambda users: None)

    def broken(users, report=True):
        raise RuntimeError("notifications down")

    monkeypatch.setattr(notify, "notify_all", broken)
    with pytest.raises(RuntimeError):
        scheduler.run_cycle()
    assert marks[0] == "task:cycle"                          # recorded before anything could fail
