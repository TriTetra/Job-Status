"""Writing to and reading from the person memory log.

`remember()` is what write paths call: it records the event inside a savepoint of the
caller's transaction, so the event and the change it describes commit together, and a
problem with the log never undoes the person's action (it is logged instead).
"""

import hashlib
import json
import logging
from datetime import date, datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from careeros.memory.models import JobImpression, PersonEvent

logger = logging.getLogger(__name__)

# What can happen with a person. An event carries intent ("skipped: pay too low"), not a
# resulting state ("score=41"); payloads hold ids and short facts, not documents.
EVENT_TYPES = {
    # who they are and what they want
    "ProfileStated", "PreferenceChanged", "WeightsChanged", "RolesChanged",
    # what they can show
    "CvUploaded", "CvRemoved", "CvPrimarySet", "EvidenceImported", "EvidenceRemoved",
    # decisions on jobs
    "JobShortlisted", "JobApplied", "JobSkipped",
    # applications over time
    "ApplicationStageChanged", "OutcomeObserved",
}
ACTORS = ("user", "agent:", "import:", "system")

# One-tap reasons on "Not for me" (critiquing: the person's own reason is worth far more than a bare skip)
SKIP_REASONS = {
    "role": "Not my kind of role",
    "skills": "Skills don't fit",
    "seniority": "Wrong level",
    "pay": "Pay too low",
    "location": "Location or visa",
    "work_style": "Remote / on-site doesn't suit me",
    "company": "Not this company",
    "applied": "Already applied elsewhere",
}

MAX_PAYLOAD_BYTES = 8_000


def job_stream(url: str) -> str:
    """Stream for everything about one job (decisions, its application): short and stable."""
    return "job:" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def clean_payload(payload: Optional[dict]) -> dict:
    """JSON-safe and small: datetimes become ISO text, oversized payloads are refused."""
    data = json.loads(json.dumps(payload or {}, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o)))
    if len(json.dumps(data)) > MAX_PAYLOAD_BYTES:
        raise ValueError("event payload too large: store a reference, not the document")
    return data


def valid_actor(actor: str) -> bool:
    return actor in ("user", "system") or actor.startswith(("agent:", "import:"))


def record(session: Session, user_id: str, type: str, payload: Optional[dict] = None, *, stream: str = "profile",
           actor: str = "user", valid_from: Optional[datetime] = None, source_ref: Optional[dict] = None,
           confidence: Optional[float] = None, causation_id: Optional[int] = None,
           correlation_id: Optional[str] = None) -> PersonEvent:
    """Append one event to the person's log (in the caller's transaction). Raises on bad input."""
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type {type!r}")
    if not valid_actor(actor):
        raise ValueError(f"unknown actor {actor!r}")
    data = clean_payload(payload)
    if session.get_bind().dialect.name == "postgresql":
        # one writer per stream at a time, so versions never collide
        session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"), {"k": f"{user_id}|{stream}"})
    version = (session.query(func.max(PersonEvent.stream_version))
               .filter(PersonEvent.user_id == user_id, PersonEvent.stream == stream).scalar() or 0) + 1
    event = PersonEvent(user_id=user_id, stream=stream, stream_version=version, type=type, payload=data, actor=actor,
                        valid_from=valid_from, source_ref=source_ref, confidence=confidence,
                        causation_id=causation_id, correlation_id=correlation_id)
    session.add(event)
    session.flush()
    return event


def remember(session: Session, user_id: str, type: str, payload: Optional[dict] = None, **kw) -> Optional[PersonEvent]:
    """record() in a savepoint: the person's action never fails because of the memory log."""
    try:
        with session.begin_nested():
            return record(session, user_id, type, payload, **kw)
    except Exception:
        logger.warning("Memory event %s for %s not recorded", type, user_id, exc_info=True)
        return None


def recent(session: Session, user_id: str, limit: int = 100, types: Optional[Iterable[str]] = None,
           before_seq: Optional[int] = None) -> list[PersonEvent]:
    """The person's latest events, newest first."""
    q = session.query(PersonEvent).filter(PersonEvent.user_id == user_id)
    if types:
        q = q.filter(PersonEvent.type.in_(list(types)))
    if before_seq:
        q = q.filter(PersonEvent.seq < before_seq)
    return q.order_by(PersonEvent.seq.desc()).limit(limit).all()


IMPRESSIONS_PER_VIEW = 50  # the first screens of a list; deeper rows were rarely seen


def log_impressions(session: Session, user_id: str, surface: str, ranked: list[tuple[str, Optional[float]]],
                    offset: int = 0, now: Optional[datetime] = None) -> int:
    """Jobs shown on `surface`, in order (rank = offset + position + 1); one row per job a day."""
    if not ranked or session.get_bind().dialect.name != "postgresql":
        return 0
    from sqlalchemy.dialects.postgresql import insert

    now = now or datetime.now(timezone.utc)
    day: date = now.date()
    rows, seen = [], set()
    for i, (url, score) in enumerate(ranked[:IMPRESSIONS_PER_VIEW]):
        if url in seen:
            continue
        seen.add(url)
        rows.append(dict(user_id=user_id, url=url, surface=surface, day=day, best_rank=offset + i + 1,
                         score=score, times=1, first_shown_at=now, last_shown_at=now))
    stmt = insert(JobImpression).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "url", "surface", "day"],
        set_=dict(best_rank=func.least(JobImpression.best_rank, stmt.excluded.best_rank),
                  times=JobImpression.times + 1, score=stmt.excluded.score, last_shown_at=stmt.excluded.last_shown_at),
    )
    try:
        with session.begin_nested():
            session.execute(stmt)
    except Exception:
        logger.warning("Impressions for %s not logged", user_id, exc_info=True)
        return 0
    return len(rows)
