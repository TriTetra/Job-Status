"""Periodic refresh: sync every company board, then rescore every active user.

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


def run_cycle() -> Optional[dict]:
    """One sync + rescore. Returns the sync totals, or None if another sync was running."""
    from careeros.identity.models.user import User
    from careeros.jobs.ingest import SyncBusy, sync_all
    from careeros.jobs.scan import run_scan, scan_jobs

    try:
        summary = sync_all()
    except SyncBusy:
        logger.info("Scheduled job sync skipped: another sync is running")
        return None

    with db.session_scope() as s:
        user_ids = [uid for (uid,) in s.query(User.id).filter(User.is_active.is_(True)).all()]
    for user_id in user_ids:
        job = scan_jobs.create(user_id, label="scheduled scan")
        run_scan(job, user_id)
        if job.status == "completed":
            r = job.result or {}
            logger.info("Rescored %s: %s scored, %s unchanged", user_id, r.get("scored"), r.get("unchanged"))
    return summary.totals


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
