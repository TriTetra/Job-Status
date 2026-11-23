"""Periodic refresh: read the job feeds (twice a day; they also discover company boards),
sync every company board, extract facts from new postings (LLM), then rescore every
active user.

Runs as a daemon thread inside the API process (JOB_SYNC_INTERVAL_HOURS > 0).
The sync's advisory lock keeps it from overlapping a manual `career-os jobs sync`;
scans only score what changed, so a cycle with nothing new is cheap.
"""

import logging
import threading
from typing import Optional

from careeros.db.connection import db

logger = logging.getLogger(__name__)

FIRST_RUN_DELAY_S = 120  # let the app finish starting (and migrations settle) first
ENRICH_PER_CYCLE = 300   # postings read by the LLM per cycle (within the bulk budget)


def run_cycle() -> Optional[dict]:
    """One sync + rescore. Returns the sync totals, or None if another sync was running."""
    from careeros.identity.models.user import User
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

    with db.session_scope() as s:
        user_ids = [uid for (uid,) in s.query(User.id).filter(User.is_active.is_(True)).all()]
    for user_id in user_ids:
        job = scan_jobs.create(user_id, label="scheduled scan")
        run_scan(job, user_id)
        if job.status == "completed":
            r = job.result or {}
            logger.info("Rescored %s: %s scored, %s unchanged", user_id, r.get("scored"), r.get("unchanged"))
    from careeros.applications.queue import prepare_all
    from careeros.notifications.notify import notify_all

    from careeros.applications.mail.sync import check_all as check_mailboxes

    check_mailboxes(user_ids)  # employers' answers move applications before the report is written
    prepare_all(user_ids)  # today's ready-to-apply kits (LLM drafts, a few per user a day)
    notify_all(user_ids)
    refresh_market_news()
    return summary.totals


def refresh_feeds() -> None:
    """Job feeds that are due (each read at most about twice a day, across restarts)."""
    from careeros.jobs.feeds import MIN_INTERVAL_H, sync_feeds

    try:
        sync_feeds(min_interval_h=MIN_INTERVAL_H)
    except Exception:
        logger.exception("Job feed sync failed")


MARKET_NEWS_EVERY = 20 * 3600  # seconds; HN "Who is hiring" + TechCrunch about once a day
_last_market_news = float("-inf")


def refresh_market_news() -> None:
    """Re-read market news once a day from the scheduler (it used to need the Refresh button)."""
    import time

    from careeros.market.refresh import run_refresh, start_refresh

    global _last_market_news
    if time.monotonic() - _last_market_news < MARKET_NEWS_EVERY:
        return
    _last_market_news = time.monotonic()
    try:
        job, created = start_refresh("scheduler")
        if created:
            run_refresh(job, 168)
            logger.info("Market news refreshed: %s", job.status)
    except Exception:
        logger.exception("Market news refresh failed")


class JobScheduler:
    def __init__(self, interval_hours: float, first_delay_s: float = FIRST_RUN_DELAY_S) -> None:
        self.interval_s = interval_hours * 3600
        self.first_delay_s = first_delay_s
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="job-scheduler", daemon=True)
        self._thread.start()
        logger.info("Job scheduler on: every %.1f h", self.interval_s / 3600)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        if self._stop.wait(self.first_delay_s):
            return
        while not self._stop.is_set():
            try:
                run_cycle()
            except Exception:
                logger.exception("Scheduled job refresh failed")
            if self._stop.wait(self.interval_s):
                return
