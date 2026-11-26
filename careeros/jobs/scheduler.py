"""Periodic refresh, in two paces:

- a tick every JOB_TICK_MINUTES (15): the company boards that are due (careeros/jobs/freshness.py:
  busy boards hourly, quiet or costly ones every 3–6 hours) and the job feeds that are due
  (about twice a day, their terms and quotas). When something new arrived: its facts (LLM),
  a rescore of every active user (only what changed is scored) and Telegram's new strong
  matches. Mailboxes are checked hourly.
- a full refresh every JOB_SYNC_INTERVAL_HOURS (6): every board, then mailboxes,
  ready-to-apply kits, notifications with the daily report, and market news (daily).

`run_auto()` does whichever is due. When each paced task last ran (full refresh, mailboxes,
market news) is kept in the database (job_board_runs, keys "task:…"), so the pace holds
across processes and restarts.

In production each run is its own short-lived process (`career-os jobs run` in the worker
service, infra/docker/worker.sh): Python keeps memory it grew into until the process ends,
so the web API stays small. For local development the API can still run it in a daemon
thread (JOB_SYNC_INTERVAL_HOURS > 0). The sync's advisory lock keeps runs from overlapping.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

from careeros.db.connection import db

logger = logging.getLogger(__name__)

FIRST_RUN_DELAY_S = 120  # let the app finish starting (and migrations settle) first
ENRICH_PER_CYCLE = 300   # postings read by the LLM per cycle (within the bulk budget)
ENRICH_PER_TICK = 80     # per tick: the new postings, so their first score already uses facts
MAIL_EVERY = timedelta(hours=1)
MARKET_NEWS_EVERY = timedelta(hours=20)  # HN "Who is hiring" + TechCrunch about once a day
TASK_CYCLE, TASK_MAIL, TASK_NEWS = "task:cycle", "task:mail", "task:market_news"


# ── when paced tasks last ran (in the database: survives processes and restarts) ──

def _now() -> datetime:
    return datetime.now(timezone.utc)


def last_run(task: str) -> Optional[datetime]:
    from careeros.jobs.models.board_run import JobBoardRun

    try:
        with db.session_scope() as s:
            row = s.get(JobBoardRun, task)
            at = row.last_run_at if row is not None else None
    except Exception:
        logger.warning("Couldn't read when %s last ran", task, exc_info=True)
        return None
    return at if at is None or at.tzinfo else at.replace(tzinfo=timezone.utc)


def is_due(task: str, every: timedelta, now: Optional[datetime] = None) -> bool:
    at = last_run(task)
    return at is None or (now or _now()) - at >= every


def mark_run(task: str, now: Optional[datetime] = None) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from careeros.jobs.models.board_run import JobBoardRun

    now = now or _now()
    try:
        with db.session_scope() as s:
            stmt = pg_insert(JobBoardRun).values(company_key=task, last_run_at=now, last_success_at=now)
            s.execute(stmt.on_conflict_do_update(index_elements=["company_key"],
                                                 set_={"last_run_at": now, "last_success_at": now}))
    except Exception:
        logger.warning("Couldn't record that %s ran", task, exc_info=True)


def full_every() -> timedelta:
    from careeros.shared.config import get_settings

    return timedelta(hours=get_settings().job_sync_interval_hours or 6)


# ── the runs ────────────────────────────────────────────────────────────

def run_cycle() -> Optional[dict]:
    """One sync + rescore. Returns the sync totals, or None if another sync was running."""
    from careeros.jobs.ingest import SyncBusy, sync_all
    from careeros.jobs.llm_extract import enrich_jobs
    from careeros.jobs.scan import run_scan, scan_jobs

    refresh_feeds()
    try:
        summary = sync_all()
    except SyncBusy:
        logger.info("Scheduled job sync skipped: another sync is running")
        return None
    try:
        enrich_jobs(ENRICH_PER_CYCLE)
    except Exception:  # scoring falls back to keyword extraction
        logger.exception("Job fact extraction failed")

    user_ids = _active_users()
    for user_id in user_ids:
        job = scan_jobs.create(user_id, label="scheduled scan")
        run_scan(job, user_id)
        if job.status == "completed":
            r = job.result or {}
            logger.info("Rescored %s: %s scored, %s unchanged", user_id, r.get("scored"), r.get("unchanged"))
    from careeros.applications.mail.sync import check_all as check_mailboxes
    from careeros.applications.queue import prepare_all
    from careeros.notifications.notify import notify_all

    check_mailboxes(user_ids)  # employers' answers move applications before the report is written
    mark_run(TASK_MAIL)
    prepare_all(user_ids)  # today's ready-to-apply kits (LLM drafts, a few per user a day)
    notify_all(user_ids)
    refresh_market_news()
    mark_run(TASK_CYCLE)
    return summary.totals


def refresh_feeds() -> int:
    """Job feeds that are due (each read at most about twice a day, across restarts). Returns new postings."""
    from careeros.jobs.feeds import MIN_INTERVAL_H, sync_feeds

    try:
        summary = sync_feeds(min_interval_h=MIN_INTERVAL_H)
        return sum(f.new for f in summary.feeds)
    except Exception:
        logger.exception("Job feed sync failed")
        return 0


def _active_users() -> list[str]:
    from careeros.identity.models.user import User

    with db.session_scope() as s:
        return [uid for (uid,) in s.query(User.id).filter(User.is_active.is_(True)).all()]


def run_tick() -> Optional[dict]:
    """The fast pace: boards and feeds that are due; when something is new, its facts, a rescore
    and Telegram's new strong matches. None if another sync was running."""
    from careeros.jobs.boards import all_boards
    from careeros.jobs.freshness import due_boards
    from careeros.jobs.ingest import SyncBusy, SyncSummary, sync_all
    from careeros.jobs.llm_extract import enrich_jobs
    from careeros.jobs.scan import run_scan, scan_jobs

    with db.session_scope() as s:
        due = due_boards(s, all_boards(s))
    new = refresh_feeds()
    try:
        summary = sync_all(due) if due else SyncSummary()
    except SyncBusy:
        logger.info("Tick skipped: another sync is running")
        return None
    new += summary.totals["new"]
    users: Optional[list[str]] = None
    if new:
        try:
            enrich_jobs(ENRICH_PER_TICK)
        except Exception:
            logger.exception("Job fact extraction failed")
        users = _active_users()
        for uid in users:
            job = scan_jobs.create(uid, label="new postings")
            run_scan(job, uid)
        from careeros.notifications.notify import notify_all

        notify_all(users, report=False)  # new strong matches within minutes; the report keeps its daily pace
        logger.info("Tick: %d board(s) read, %d new posting(s)", len(due), new)
    if is_due(TASK_MAIL, MAIL_EVERY):
        from careeros.applications.mail.sync import check_all as check_mailboxes

        check_mailboxes(users if users is not None else _active_users())
        mark_run(TASK_MAIL)
    return {"boards": len(due), "new": new}


def run_auto() -> tuple[str, Optional[dict]]:
    """The full refresh when it is due, else a tick: ("cycle" | "tick", result)."""
    if is_due(TASK_CYCLE, full_every()):
        return "cycle", run_cycle()
    return "tick", run_tick()


def refresh_market_news() -> None:
    """Re-read market news once a day from the scheduler (it used to need the Refresh button)."""
    from careeros.market.refresh import run_refresh, start_refresh

    if not is_due(TASK_NEWS, MARKET_NEWS_EVERY):
        return
    mark_run(TASK_NEWS)
    try:
        job, created = start_refresh("scheduler")
        if created:
            run_refresh(job, 168)
            logger.info("Market news refreshed: %s", job.status)
    except Exception:
        logger.exception("Market news refresh failed")


class JobScheduler:
    """In-process scheduling (local development). Production runs `career-os jobs run` in a worker."""

    def __init__(self, interval_hours: float, tick_minutes: float = 15, first_delay_s: float = FIRST_RUN_DELAY_S) -> None:
        self.interval_s = interval_hours * 3600
        self.tick_s = tick_minutes * 60 if tick_minutes > 0 else self.interval_s
        self.first_delay_s = first_delay_s
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="job-scheduler", daemon=True)
        self._thread.start()
        logger.info("Job scheduler on: due boards every %.0f min, everything every %.1f h",
                    self.tick_s / 60, self.interval_s / 3600)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        if self._stop.wait(self.first_delay_s):
            return
        while not self._stop.is_set():
            try:
                run_auto()
            except Exception:
                logger.exception("Scheduled job refresh failed")
            if self._stop.wait(self.tick_s):
                return
