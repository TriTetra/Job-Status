"""Read side of job intelligence: a user's scored opportunities and their reasoning."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from core.db.models.application import Application
from core.db.models.career_score import CareerScore
from core.db.repositories import CareerScoreRepository
from core.db.repositories.career_preferences_repo import CareerPreferencesRepository

from .decision_builder import build_decision, reasoning_for

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
        text, source = reasoning_for(explanation, decision, matched, gaps)
        decision.update(reasoning=text, reasoning_source=source, generated_at=datetime.utcnow().isoformat())
        explanation["decision"] = decision
        score.explanation = explanation
        session.commit()

    return decision
