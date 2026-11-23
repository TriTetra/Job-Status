"""How often each source is read, so a new posting reaches people within the hour where that's cheap.

Company boards (one free request each, read from the employer's own hiring system):
- a list API that returns the whole board in one call (Greenhouse, Lever, Ashby, Workable,
  Recruitee, Personio): every hour while the board is adding roles (a new one in the last
  ACTIVE_DAYS), else every 3 hours;
- systems that need a request per posting (SmartRecruiters, Workday, Eightfold): every 3 hours
  while active, else every 6;
- a board whose last read failed waits 6 hours (it isn't hammered).
Job feeds keep their own pace (careeros/jobs/feeds.py MIN_INTERVAL_H: their terms and quotas).

`lag()` measures it: hours between a posting's own date and when Aplio first saw it.
"""

from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from careeros.jobs.models.board_run import JobBoardRun
from careeros.jobs.models.job import Job

CHEAP = {"greenhouse", "lever", "ashby", "workable", "recruitee", "personio"}
ACTIVE_DAYS = 14
HOUR = timedelta(hours=1)
INTERVAL = {  # (active, quiet)
    "cheap": (HOUR, 3 * HOUR),
    "costly": (3 * HOUR, 6 * HOUR),
}
FAILED_WAIT = 6 * HOUR
GRACE = timedelta(minutes=5)   # a board read 55 minutes ago is due at the hourly tick


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def interval(ats: str, active: bool, failed: bool) -> timedelta:
    if failed:
        return FAILED_WAIT
    fast, slow = INTERVAL["cheap" if ats in CHEAP else "costly"]
    return fast if active else slow


def due_boards(session: Session, boards: Iterable, now: Optional[datetime] = None) -> list[str]:
    """Keys of the boards whose next read is due now (never read: due)."""
    now = now or datetime.now(timezone.utc)
    boards = list(boards)
    keys = [b.key for b in boards]
    runs = {r.company_key: r for r in session.query(JobBoardRun).filter(JobBoardRun.company_key.in_(keys)).all()}
    recent = {k for (k,) in session.query(Job.company_key)
              .filter(Job.company_key.in_(keys), Job.discovered_at >= now - timedelta(days=ACTIVE_DAYS))
              .group_by(Job.company_key).all()}
    due = []
    for b in boards:
        run = runs.get(b.key)
        if run is None:
            due.append(b.key)
            continue
        wait = interval(b.ats, b.key in recent, bool(run.last_error))
        if now - _aware(run.last_run_at) + GRACE >= wait:
            due.append(b.key)
    return due


def lag(session: Session, days: int = 7, now: Optional[datetime] = None) -> dict:
    """How fast new postings reach Aplio: hours from the posting's own date to first seen (company boards)."""
    now = now or datetime.now(timezone.utc)
    rows = (session.query(Job.posted_at, Job.discovered_at)
            .filter(Job.ats.isnot(None), Job.posted_at.isnot(None), Job.added_by.is_(None),
                    Job.discovered_at >= now - timedelta(days=days),
                    Job.posted_at >= now - timedelta(days=days)).all())
    hours = sorted(max(0.0, (_aware(d) - _aware(p)).total_seconds() / 3600) for p, d in rows if p and d)
    runs = session.query(func.count(JobBoardRun.company_key), func.max(JobBoardRun.last_run_at)).one()
    out = {"days": days, "postings": len(hours), "boards": runs[0] or 0,
           "last_read": _aware(runs[1]).isoformat() if runs[1] else None}
    if len(hours) >= 5:
        out["median_hours"] = round(median(hours), 1)
        out["p90_hours"] = round(hours[int(len(hours) * 0.9) - 1], 1)
    return out
