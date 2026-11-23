"""Your applications as a pipeline, and what it says about your search.

`pipeline()` is the board: every tracked application (not the ones you passed on)
with what the job board and your score add: logo key, location, score, how long it
has sat in its stage. `analytics()` reads the same rows plus each one's status
history: the funnel, weekly pace, how often an application hears back, and whether
your stronger matches convert better.
"""

from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job

DAY = timedelta(days=1)
WEEK = timedelta(days=7)
WEEKS = 8
STALE_AFTER_DAYS = 14  # an application with no word for two weeks deserves a follow-up
ON_BOARD = ("to_apply", "applied", "interview", "offer")
CLOSED = ("rejected", "withdrawn")
APPLIED_OR_LATER = ("applied", "interview", "offer")
BANDS = (("70+", 70, 1000), ("55–69", 55, 70), ("Under 55", -1, 55))


def _parse(at: Optional[str]) -> Optional[datetime]:
    if not at:
        return None
    try:
        d = datetime.fromisoformat(at)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def reached(app: Application) -> set[str]:
    """Every status this application has been in (history, current status, applied_at)."""
    seen = {e.get("status") for e in (app.history or []) if isinstance(e, dict)}
    seen.add(app.status)
    if app.applied_at:
        seen.add("applied")
    if seen & {"interview", "offer"}:
        seen.add("applied")
    if "offer" in seen:
        seen.add("interview")
    return seen


def since_last_move(app: Application) -> Optional[datetime]:
    """When it entered its current status."""
    for e in reversed(app.history or []):
        if isinstance(e, dict) and e.get("status") == app.status:
            return _parse(e.get("at"))
    return _aware(app.updated_at)


def _jobs(session: Session, urls: Iterable[str]) -> dict[str, Job]:
    urls = list(urls)
    return {j.url: j for j in session.query(Job).filter(Job.url.in_(urls)).all()} if urls else {}


def _scores(session: Session, user_id: str, urls: Iterable[str]) -> dict[str, CareerScore]:
    urls = list(urls)
    if not urls:
        return {}
    rows = session.query(CareerScore).filter(CareerScore.user_id == user_id, CareerScore.url.in_(urls)).all()
    return {s.url: s for s in rows}


def _apps(session: Session, user_id: str) -> list[Application]:
    return (session.query(Application).filter(Application.user_id == user_id)
            .order_by(Application.updated_at.desc()).all())


def _iso(d: Optional[datetime]) -> Optional[str]:
    return _aware(d).isoformat() if d else None


def pipeline(session: Session, user_id: str, now: Optional[datetime] = None) -> list[dict]:
    """The board and the closed list: one row per application you didn't pass on."""
    now = now or datetime.now(timezone.utc)
    apps = [a for a in _apps(session, user_id) if a.status != "skipped"]
    jobs = _jobs(session, (a.url for a in apps))
    scores = _scores(session, user_id, (a.url for a in apps))
    from careeros.applications.followup import states

    follow = states(session, user_id, apps, now)
    out = []
    for a in apps:
        job, score = jobs.get(a.url), scores.get(a.url)
        moved = since_last_move(a)
        days = int((now - moved) / DAY) if moved else None
        out.append({
            "url": a.url,
            "title": a.title,
            "company": a.company or (job.company if job else None),
            "company_key": job.company_key if job else None,
            "status": a.status,
            "applied_at": _iso(a.applied_at),
            "notes": a.notes,
            "created_at": _iso(a.created_at),
            "updated_at": _iso(a.updated_at),
            "history": [e for e in (a.history or []) if isinstance(e, dict)],
            "days_in_status": days,
            "stale": a.status == "applied" and days is not None and days >= STALE_AFTER_DAYS,
            "location": (job.location if job else None),
            "remote": bool(job.remote) if job else False,
            "posting_closed": bool(job and job.closed_at),
            "application_url": (job.application_url or job.url) if job else a.url,
            "score": round(score.career_score) if score and score.career_score is not None else None,
            "recommendation": (score.recommendation or "").split(" - ")[0].upper() if score else None,
            "follow_up": follow.get(a.url),
        })
    return out


def _open_matches(session: Session, user_id: str) -> int:
    rows = (session.query(CareerScore.recommendation).join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None)).all())
    return sum(1 for (rec,) in rows if (rec or "").upper().startswith(("APPLY", "CONSIDER")))


def analytics(session: Session, user_id: str, now: Optional[datetime] = None) -> dict:
    """The funnel from match to offer, weekly pace, response rate, and score vs outcome."""
    now = now or datetime.now(timezone.utc)
    apps = _apps(session, user_id)
    tracked = [a for a in apps if a.status != "skipped"]
    stages = {a.url: reached(a) for a in tracked}
    applied = [a for a in tracked if "applied" in stages[a.url]]
    interviews = [a for a in tracked if "interview" in stages[a.url]]
    offers = [a for a in tracked if "offer" in stages[a.url]]

    weekly = [0] * WEEKS
    for a in applied:
        at = _aware(a.applied_at)
        if at:
            age = int((now - at) / WEEK)
            if 0 <= age < WEEKS:
                weekly[WEEKS - 1 - age] += 1

    # Heard back: of applications sent at least two weeks ago, how many got any answer
    old_enough = [a for a in applied if a.applied_at and now - _aware(a.applied_at) >= STALE_AFTER_DAYS * DAY]
    answered = [a for a in old_enough if stages[a.url] & {"interview", "offer", "rejected"}]
    waiting = [a for a in tracked if a.status == "applied"]
    waiting_days = [int((now - m) / DAY) for a in waiting if (m := since_last_move(a))]

    scores = _scores(session, user_id, (a.url for a in applied))
    bands = []
    for label, lo, hi in BANDS:
        in_band = [a for a in applied if a.url in scores and scores[a.url].career_score is not None
                   and lo <= scores[a.url].career_score < hi]
        bands.append({"band": label, "applied": len(in_band),
                      "interviews": sum(1 for a in in_band if "interview" in stages[a.url])})

    def rate(part: int, whole: int) -> Optional[float]:
        return round(part / whole, 2) if whole else None

    return {
        "open_matches": _open_matches(session, user_id),
        "funnel": [
            {"stage": "tracked", "count": len(tracked)},
            {"stage": "applied", "count": len(applied)},
            {"stage": "interview", "count": len(interviews)},
            {"stage": "offer", "count": len(offers)},
        ],
        "interview_rate": rate(len(interviews), len(applied)),
        "offer_rate": rate(len(offers), len(interviews)),
        "weekly_applied": weekly,
        "applied_this_week": weekly[-1],
        "response": {"rate": rate(len(answered), len(old_enough)), "answered": len(answered),
                     "sent": len(old_enough)},
        "waiting": {"count": len(waiting), "median_days": int(median(waiting_days)) if waiting_days else None,
                    "stale": sum(1 for d in waiting_days if d >= STALE_AFTER_DAYS)},
        "by_score": bands,
        "closed": {"rejected": sum(1 for a in tracked if a.status == "rejected"),
                   "withdrawn": sum(1 for a in tracked if a.status == "withdrawn")},
        "passed_on": sum(1 for a in apps if a.status == "skipped"),
    }
