"""Read side of job intelligence: a user's scored opportunities and their reasoning."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.applications.repositories.application_repo import ApplicationRepository
from careeros.jobs.models.job import Job
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.repositories.career_score_repo import CareerScoreRepository
from careeros.identity.repositories.career_preferences_repo import CareerPreferencesRepository

from careeros.jobs.decision_builder import build_decision, reasoning_for

# Application pipeline status → the user's decision on an opportunity
DECISION_BY_APPLICATION_STATUS = {
    "to_apply": "shortlisted",
    "applied": "applied",
    "interview": "interviewing",
    "offer": "offer",
    "skipped": "skipped",
    "rejected": "skipped",
    "withdrawn": "skipped",
}
UNREVIEWED = {"status": "unreviewed", "decided_at": None}
# What the inbox buttons may record: Shortlist, Apply, Skip
DECIDABLE_STATUSES = ("to_apply", "applied", "skipped")


class UnknownJob(LookupError):
    """The job URL isn't in the jobs table."""


DECISION_EVENTS = {"to_apply": "JobShortlisted", "applied": "JobApplied", "skipped": "JobSkipped"}


def _belief_at_decision(session: Session, user_id: str, url: str, shown: Optional[dict] = None) -> dict:
    """What Aplio believed when the person decided (the label for learning, with its context):
    the saved score, else what the screen showed (a search result scored on the fly)."""
    try:
        score = CareerScoreRepository(session).get_latest_score(url=url, user_id=user_id)
    except Exception:
        score = None
    if score is not None:
        model = (getattr(score, "explanation", None) or {}).get("model") or {}
        return {"score": getattr(score, "career_score", None), "p_interview": model.get("p_effective"),
                "value": model.get("value"), "belief": "saved"}
    shown = {k: v for k, v in (shown or {}).items() if v is not None}
    return {**shown, "belief": "shown"} if shown else {}


def record_decision(session: Session, user_id: str, url: str, status: str, reasons: Optional[List[str]] = None,
                    surface: Optional[str] = None, shown: Optional[dict] = None) -> dict:
    """Shortlist / Apply / Skip an opportunity: create its application row if needed
    (title and company from the posting), then move it to `status`. The decision, with the
    person's reasons for a skip and where it was made, goes to their memory log.

    Returns the new user decision {"status", "decided_at"}.
    """
    from careeros.memory.events import SKIP_REASONS, job_stream, remember

    if status not in DECIDABLE_STATUSES:
        raise ValueError(f"status must be one of {', '.join(DECIDABLE_STATUSES)}")
    job = session.get(Job, url)
    if job is None:
        raise UnknownJob(url)
    remember(session, user_id, DECISION_EVENTS[status], {
        "url": url, "title": job.title, "company": job.company, "surface": surface,
        "reasons": [r for r in (reasons or []) if r in SKIP_REASONS] if status == "skipped" else [],
        **_belief_at_decision(session, user_id, url, shown),
    }, stream=job_stream(url))
    repo = ApplicationRepository(session)
    app = repo.upsert(url=url, title=job.title or "Untitled role", company=job.company or None,
                      status=status, user_id=user_id)
    if status == "applied":
        app = repo.mark_applied(url, user_id=user_id) or app
    elif app.status != status:
        app = repo.advance_status(url, status, user_id=user_id) or app
    decided = getattr(app, "updated_at", None) or datetime.utcnow()
    return {"status": DECISION_BY_APPLICATION_STATUS[status], "decided_at": decided.isoformat()}


def user_decisions(session: Session, user_id: str) -> Dict[str, dict]:
    """{job url: {"status", "decided_at"}} from the user's applications (one query)."""
    rows = (
        session.query(Application.url, Application.status, Application.updated_at)
        .filter(Application.user_id == user_id)
        .all()
    )
    return {
        url: {
            "status": DECISION_BY_APPLICATION_STATUS.get(status, "skipped"),
            "decided_at": updated.isoformat() if updated else None,
        }
        for url, status, updated in rows
    }


def list_opportunities(session: Session, user_id: str, recommendation: str = "ALL", limit: int = 200) -> List[CareerScore]:
    """Latest score per job, best first. Scoring classifies opportunities; it never hides them."""
    return CareerScoreRepository(session).get_top_opportunities(
        min_score=None,
        recommendation=None if recommendation == "ALL" else recommendation,
        limit=limit,
        user_id=user_id,
    )


def count_opportunities(session: Session, user_id: str, recommendation: str = "ALL") -> int:
    """Total matching jobs, independent of the list limit."""
    return CareerScoreRepository(session).count_latest(user_id, None if recommendation == "ALL" else recommendation)


def get_opportunity(session: Session, user_id: str, url: str) -> Optional[CareerScore]:
    return CareerScoreRepository(session).get_latest_score(url=url, user_id=user_id)


def _decision_prefs(session: Session, user_id: str) -> dict:
    p = CareerPreferencesRepository(session).get_by_user_id(user_id)
    if not p:
        return {}
    return {
        "work_arrangements": p.work_arrangements or [],
        "preferred_country_codes": p.preferred_country_codes or [],
        "requires_sponsorship": p.requires_sponsorship,
        "salary_min": p.salary_min,
        "salary_max": p.salary_max,
    }


def _person_facts(session: Session, user_id: str) -> dict:
    """Who the person is, for the deeper read to check a job against: where they live, what
    they want, how experienced they are."""
    from careeros.identity.models.user import User

    facts = _decision_prefs(session, user_id)
    p = CareerPreferencesRepository(session).get_by_user_id(user_id)
    if p is not None:
        facts["salary_currency"] = p.salary_currency
    user = session.get(User, user_id)
    if user is not None:
        data = user.profile_data or {}
        facts.update(country=data.get("country"), years=data.get("total_years") or user.years_in_role,
                     level=user.career_level)
    return facts


def get_or_create_reasoning(session: Session, user_id: str, url: str) -> Optional[dict]:
    """The opportunity's decision with its reasoning (LLM, template fallback), cached on the score row.

    Returns None if the user has no score for this URL.
    """
    score = get_opportunity(session, user_id, url)
    if not score:
        return None

    explanation = dict(score.explanation or {})
    decision = explanation.get("decision")
    matched = explanation.get("matched_skills") or []
    gaps = score.skill_gaps or []

    if not decision:  # rows scored before Decision Contract v1
        decision = build_decision(
            recommendation=score.recommendation,
            career_score=score.career_score or 0,
            career_value=score.career_value or 0,
            market_demand=score.market_demand or 0,
            job=explanation,
            prefs=_decision_prefs(session, user_id),
            matched_skills=matched,
            gap_skills=gaps,
        )

    if not decision.get("reasoning"):
        text, source = reasoning_for(explanation, decision, matched, gaps, user_id, _person_facts(session, user_id))
        decision.update(reasoning=text, reasoning_source=source, generated_at=datetime.utcnow().isoformat())
        explanation["decision"] = decision
        score.explanation = explanation
        session.commit()

    return decision
