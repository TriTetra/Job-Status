"""Today's ready-to-apply queue: the few best jobs to send today, each with its apply kit.

Picked from the person's scored matches: open, not decided yet, not ruled out, from a
trustworthy employer, recent enough to still be hiring, one per company, best score first.
The scheduler prepares their kits once a day; the person reviews and submits each one.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.applications.models.apply_kit import ApplyKit
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job

logger = logging.getLogger(__name__)

QUEUE_SIZE = 5
MIN_SCORE = 65
MAX_AGE_DAYS = 30
CANDIDATES = 200


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def eligible(score: CareerScore, job: Job, now: datetime) -> bool:
    """Worth sending today: a real recommendation, nothing ruling it out, a trustworthy employer, fresh."""
    rec = (score.recommendation or "").split(" - ")[0].strip().upper()
    if rec not in ("APPLY", "CONSIDER") or (score.career_score or 0) < MIN_SCORE:
        return False
    ex = score.explanation or {}
    model = ex.get("model") or {}
    if model.get("gates"):
        return False
    trust = ex.get("trust") or {}
    if trust.get("level") == "risk" or trust.get("agency"):
        return False
    seen = _aware(job.posted_at) or _aware(job.discovered_at)
    return not seen or now - seen <= timedelta(days=MAX_AGE_DAYS)


def pick(session: Session, user_id: str, n: int = QUEUE_SIZE, now: Optional[datetime] = None) -> list[tuple[CareerScore, Job]]:
    now = now or datetime.now(timezone.utc)
    decided = {u for (u,) in session.query(Application.url).filter(Application.user_id == user_id).all()}
    rows = (session.query(CareerScore, Job).join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None))
            .order_by(CareerScore.career_score.desc().nullslast()).limit(CANDIDATES).all())
    out, companies = [], set()
    for s, j in rows:
        company = (j.company or "").strip().lower()
        if s.url in decided or company in companies or not eligible(s, j, now):
            continue
        companies.add(company)
        out.append((s, j))
        if len(out) >= n:
            break
    return out


def _item(score: CareerScore, job: Job, kit: Optional[dict]) -> dict:
    ex = score.explanation or {}
    model = ex.get("model") or {}
    return {
        "url": job.url, "title": job.title, "company": job.company, "location": job.location,
        "company_key": job.company_key, "score": score.career_score, "recommendation": score.recommendation,
        "p_interview": model.get("p_effective"), "apply_url": job.application_url or job.url,
        "trust": ex.get("trust"), "ready": bool(kit), "kit": kit,
    }


def today(session: Session, user_id: str, n: int = QUEUE_SIZE, now: Optional[datetime] = None) -> list[dict]:
    """Today's queue with whatever kits are ready (kits are built by prepare() or on request)."""
    picks = pick(session, user_id, n, now)
    kits = {k.url: k.payload for k in session.query(ApplyKit).filter(
        ApplyKit.user_id == user_id, ApplyKit.url.in_([j.url for _, j in picks])).all()} if picks else {}
    return [_item(s, j, kits.get(j.url)) for s, j in picks]


def prepare(session: Session, user_id: str, n: int = QUEUE_SIZE, now: Optional[datetime] = None) -> int:
    """Build the kits today's queue is missing. Returns how many were built."""
    from careeros.applications.kit import build_kit

    built = 0
    for s, j in pick(session, user_id, n, now):
        if session.get(ApplyKit, (user_id, j.url)) is not None:
            continue
        try:
            build_kit(session, user_id, j.url, now=now)
            session.commit()
            built += 1
        except Exception:
            session.rollback()
            logger.exception("Apply kit failed for %s / %s", user_id, j.url)
    return built


def prepare_all(user_ids: list[str]) -> None:
    """Scheduler hook: one session per user; failures are logged, never raised."""
    from careeros.db.connection import db

    for uid in user_ids:
        try:
            with db.session_scope() as s:
                n = prepare(s, uid)
            if n:
                logger.info("Apply queue: %d kit(s) prepared for %s", n, uid)
        except Exception:
            logger.exception("Apply queue failed for %s", uid)
