"""Gather everything the briefing needs for one user, in one call."""

from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.companies.models.company import Company
from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.identity.models.career_preferences import CareerPreferences
from careeros.identity.models.connected_account import ConnectedAccount
from careeros.identity.models.user import User
from careeros.jobs.models.career_score import CareerScore

TOP_OPPORTUNITIES = 2
HIRING_COMPANIES = 3
LIVE_APPLICATIONS = 3
TONES = {"warm", "direct", "analytical"}


def _top_opportunities(session: Session, user_id: str) -> list[dict]:
    """Latest score per URL, APPLY/CONSIDER only, best first."""
    latest = (
        select(CareerScore.url, func.max(CareerScore.scanned_at).label("latest"))
        .where(CareerScore.user_id == user_id)
        .group_by(CareerScore.url)
        .subquery()
    )
    rows = session.execute(
        select(CareerScore)
        .join(latest, and_(CareerScore.url == latest.c.url, CareerScore.scanned_at == latest.c.latest))
        .where(
            CareerScore.user_id == user_id,
            # prefix: older rows store the full scorer text ("APPLY - Good fit")
            or_(CareerScore.recommendation.startswith("APPLY"), CareerScore.recommendation.startswith("CONSIDER")),
        )
        .order_by(CareerScore.career_score.desc())
        .limit(TOP_OPPORTUNITIES)
    ).scalars()
    return [
        {
            "url": s.url,
            "career_score": s.career_score,
            "recommendation": s.recommendation,
            "skill_gaps": s.skill_gaps or [],
            "explanation": s.explanation or {},
        }
        for s in rows
    ]


def _evidence_counts(session: Session, user_id: str) -> dict:
    items = session.query(EvidenceItem.confidence_score, EvidenceItem.evidence_data).filter(
        EvidenceItem.user_id == user_id
    ).all()
    skills = sum(1 for _, data in items if (data or {}).get("type", "skill") == "skill")
    avg = sum(c or 0 for c, _ in items) / len(items) if items else 0.0
    return {"total": len(items), "skill_count": skills, "avg_confidence": round(avg, 4)}


def get_briefing_facts(session: Session, user_id: str) -> dict:
    since = func.now() - timedelta(hours=24)  # DB clock, same as the timestamps it compares

    user = session.query(User).filter(User.clerk_id == user_id).first()
    profile = (user.profile_data if user else None) or {}

    companies = (
        session.query(Company)
        .filter(Company.hiring_trend.in_(("up", "spike")), Company.open_positions_count > 0)
        .order_by(Company.open_positions_count.desc())
        .limit(HIRING_COMPANIES)
        .all()
    )
    live_apps = (
        session.query(Application.company, Application.title, Application.status)
        .filter(Application.user_id == user_id, Application.status.in_(("interview", "offer")))
        .limit(LIVE_APPLICATIONS)
        .all()
    )
    github_connected = session.query(ConnectedAccount.id).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "github",
        ConnectedAccount.is_active.is_(True),
    ).first() is not None
    prefs = session.query(CareerPreferences.pref_metadata).filter(CareerPreferences.user_id == user_id).first()
    tone = ((prefs[0] if prefs else None) or {}).get("communication_style")

    return {
        "first_name": profile.get("first_name"),
        "career_graph_stats": (profile.get("career_graph") or {}).get("stats") or {},
        "opportunities": _top_opportunities(session, user_id),
        "evidence": _evidence_counts(session, user_id),
        "hiring_companies": [
            {"name": c.name, "hiring_trend": c.hiring_trend, "open_positions_count": c.open_positions_count}
            for c in companies
        ],
        "last_24h": {
            "new_evidence": session.query(EvidenceItem).filter(
                EvidenceItem.user_id == user_id, EvidenceItem.created_at > since
            ).count(),
            "new_scores": session.query(CareerScore).filter(
                CareerScore.user_id == user_id, CareerScore.scanned_at > since
            ).count(),
        },
        "live_applications": [{"company": c, "title": t, "status": s} for c, t, s in live_apps],
        "github_connected": github_connected,
        "tone": tone if tone in TONES else "warm",
    }
