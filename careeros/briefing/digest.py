"""Briefing v2: what changed since the user's last visit, and what to do about it.

Everything here is computed from data the system already keeps (scores, jobs,
applications, evidence). The web app turns it into sentences; no LLM is called
on page load — the headline reuses the cached "why" when there is one.

Visits: `users.profile_data.briefing_seen = {"at", "prev"}`. A visit more than
VISIT_GAP after the last one starts a new window, so a reload doesn't reset
"since your last visit" to zero minutes.

Dismissed to-dos: `profile_data.briefing_dismissed = {key: iso time}`, hidden
for DISMISS_FOR.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from careeros.applications.models.application import Application
from careeros.briefing.facts import TONES, _evidence_counts, _top_opportunities
from careeros.identity.models.career_preferences import CareerPreferences
from careeros.identity.models.connected_account import ConnectedAccount
from careeros.identity.models.user import User
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job

VISIT_GAP = timedelta(hours=2)
FIRST_WINDOW = timedelta(hours=24)
DISMISS_FOR = timedelta(days=7)
FOLLOW_UP_AFTER = timedelta(days=10)
SHORTLIST_STALE_AFTER = timedelta(days=3)
MIN_GAP_COUNT = 3
MAX_TODOS = 4
MATCH_RECS = ("APPLY", "CONSIDER")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _naive(dt: datetime) -> datetime:
    """For DateTime columns stored without a zone (UTC by convention)."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _parse(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _days(delta: timedelta) -> int:
    return max(1, delta.days)


def record_visit(user: Optional[User], now: datetime) -> tuple[datetime, Optional[float]]:
    """(window start, hours since the previous visit or None) — and remember this visit."""
    if user is None:
        return now - FIRST_WINDOW, None
    data = dict(user.profile_data or {})
    seen = dict(data.get("briefing_seen") or {})
    last, prev = _parse(seen.get("at")), _parse(seen.get("prev"))
    if last is None:
        seen = {"at": now.isoformat(), "prev": None}
        since, hours = now - FIRST_WINDOW, None
    elif now - last > VISIT_GAP:
        seen = {"at": now.isoformat(), "prev": last.isoformat()}
        since, hours = last, (now - last).total_seconds() / 3600
    else:  # a reload within the same visit keeps the window it started with
        since = prev or now - FIRST_WINDOW
        hours = (now - prev).total_seconds() / 3600 if prev else None
    data["briefing_seen"] = seen
    user.profile_data = data
    flag_modified(user, "profile_data")
    return since, hours


def dismiss(session: Session, user_id: str, key: str, now: Optional[datetime] = None) -> None:
    """Hide a to-do for DISMISS_FOR."""
    user = session.query(User).filter(User.id == user_id).first()
    if user is None:
        return
    data = dict(user.profile_data or {})
    now = now or _utcnow()
    dismissed = {k: v for k, v in (data.get("briefing_dismissed") or {}).items()
                 if (_parse(v) or now) > now - DISMISS_FOR}
    dismissed[key[:200]] = now.isoformat()
    data["briefing_dismissed"] = dismissed
    user.profile_data = data
    flag_modified(user, "profile_data")


def _chance(acceptance: Optional[float]) -> str:
    a = acceptance or 0  # stored as 0–100
    return "high" if a >= 30 else "medium" if a >= 15 else "low"


def _headline(session: Session, user_id: str) -> Optional[dict]:
    tops = _top_opportunities(session, user_id)
    if not tops:
        return None
    top = tops[0]
    score = session.query(CareerScore).filter(CareerScore.user_id == user_id, CareerScore.url == top["url"]).first()
    job = session.get(Job, top["url"])
    ex = top["explanation"] or {}
    decision = ex.get("decision") or {}
    matched = [m.get("name") if isinstance(m, dict) else str(m) for m in ex.get("matched_skills") or []]
    return {
        "url": top["url"],
        "company": ex.get("company") or (job.company if job else ""),
        "company_key": ex.get("company_key") or (job.company_key if job else None),
        "title": ex.get("title") or (job.title if job else "Open role"),
        "location": ex.get("location") or (job.location if job else ""),
        "remote": bool(ex.get("remote")),
        "score": round(top["career_score"] or 0),
        "recommendation": (top["recommendation"] or "CONSIDER").split(" - ")[0].upper(),
        "chance": _chance(score.acceptance_probability if score else None),
        "reasoning": decision.get("reasoning"),
        "next_action": (decision.get("next_action") or {}).get("reason"),
        "criteria": [{"label": c.get("label"), "state": c.get("state"), "detail": c.get("detail")}
                     for c in decision.get("criteria") or []],
        "matched": [m for m in matched if m][:5],
        "gaps": list(top["skill_gaps"] or [])[:3],
        "posted_at": (job.posted_at.isoformat() if job and job.posted_at else ex.get("posted_at")),
        "salary": ({"min": job.salary_min, "max": job.salary_max, "currency": job.salary_currency or "USD"}
                   if job and (job.salary_min or job.salary_max) else None),
        "application_url": ex.get("application_url") or (job.application_url if job else None) or top["url"],
        "summary": ex.get("summary"),
    }


def _open_matches(session: Session, user_id: str):
    return (
        session.query(CareerScore, Job)
        .join(Job, Job.url == CareerScore.url)
        .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None),
                or_(*(CareerScore.recommendation.ilike(f"{r}%") for r in MATCH_RECS)))
    )


def _changes(session: Session, user_id: str, since: datetime) -> dict:
    new = _open_matches(session, user_id).filter(CareerScore.first_scored_at > _naive(since)).all()
    companies = Counter(j.company for _, j in new if j.company)
    closed = (
        session.query(Application.company, Application.title)
        .join(Job, Job.url == Application.url)
        .filter(Application.user_id == user_id, Application.status.in_(("to_apply", "applied")),
                Job.closed_at.isnot(None), Job.closed_at > since)
        .limit(3).all()
    )
    return {
        "new_matches": len(new),
        "new_strong": sum(1 for s, _ in new if (s.recommendation or "").upper().startswith("APPLY")),
        "busy_companies": [{"name": n, "count": c} for n, c in companies.most_common(3) if c >= 2],
        "closed_tracked": [{"company": c or "", "title": t} for c, t in closed],
    }


def _week(session: Session, user_id: str, now: datetime) -> dict:
    week_ago, two_weeks = _naive(now - timedelta(days=7)), _naive(now - timedelta(days=14))
    strong = _open_matches(session, user_id).filter(CareerScore.recommendation.ilike("APPLY%"))
    return {
        "strong_this_week": strong.filter(CareerScore.first_scored_at > week_ago).count(),
        "strong_last_week": strong.filter(CareerScore.first_scored_at > two_weeks,
                                          CareerScore.first_scored_at <= week_ago).count(),
        "applied_this_week": session.query(Application).filter(
            Application.user_id == user_id, Application.applied_at > now - timedelta(days=7)).count(),
        "open_strong": strong.count(),
        "open_matches": _open_matches(session, user_id).count(),
    }


def _todos(session: Session, user_id: str, now: datetime, dismissed: dict, has_scores: bool,
           sources_connected: bool, skill_count: int) -> list[dict]:
    todos: list[dict] = []
    live = (session.query(Application).filter(Application.user_id == user_id,
                                              Application.status.in_(("offer", "interview")))
            .order_by(Application.updated_at.desc()).limit(2).all())
    for a in live:
        offer = a.status == "offer"
        todos.append({
            "key": f"{a.status}:{a.url}",
            "kind": a.status,
            "title": f"{'Your offer from' if offer else 'Prepare for'} {a.company or a.title}",
            "detail": a.title if offer else f"{a.title} — interviewing now.",
            "cta_label": "Open applications", "cta_href": "/applications",
        })

    if not has_scores:
        todos.append({
            "key": "first_scan", "kind": "scan",
            "title": "Run your first opportunity scan",
            "detail": f"{skill_count} skills ready to match against open roles from 74 company boards.",
            "cta_label": "Scan now", "cta_href": "/inbox?scan=1",
        })

    waiting = (session.query(Application).filter(
        Application.user_id == user_id, Application.status == "applied",
        Application.applied_at.isnot(None), Application.applied_at < now - FOLLOW_UP_AFTER)
        .order_by(Application.applied_at).limit(2).all())
    for a in waiting:
        todos.append({
            "key": f"followup:{a.url}", "kind": "followup",
            "title": f"No reply from {a.company or 'them'} in {_days(now - a.applied_at)} days",
            "detail": f"{a.title}. A short follow-up note is normal after ten days.",
            "cta_label": "Open applications", "cta_href": "/applications",
        })

    shortlisted = (session.query(Application, Job).outerjoin(Job, Job.url == Application.url).filter(
        Application.user_id == user_id, Application.status == "to_apply",
        Application.created_at < now - SHORTLIST_STALE_AFTER)
        .order_by(Application.created_at).limit(1).all())
    for a, j in shortlisted:
        closed = j is not None and j.closed_at is not None
        todos.append({
            "key": f"shortlist:{a.url}", "kind": "shortlist",
            "title": f"You shortlisted {a.company or a.title} {_days(now - a.created_at)} days ago",
            "detail": "It has closed since." if closed else f"{a.title} — still open. Apply or let it go.",
            "cta_label": "Open applications" if closed else "Open posting",
            "cta_href": "/applications" if closed else ((j.application_url if j else None) or a.url),
            "external": not closed,
        })

    gaps = Counter()
    for s, _ in _open_matches(session, user_id).all():
        for g in s.skill_gaps or []:
            gaps[str(g)] += 1
    if gaps:
        skill, n = gaps.most_common(1)[0]
        if n >= MIN_GAP_COUNT:
            todos.append({
                "key": f"gap:{skill.lower()}", "kind": "gap",
                "title": f"{skill} is missing in {n} of your matches",
                "detail": "It's the skill your matches ask for most that your evidence doesn't show. "
                          "Proof of it (a repo, a project, a course) lifts all of them.",
                "cta_label": "Add proof", "cta_href": "/settings?tab=account",
            })

    if not sources_connected:
        todos.append({
            "key": "connect_sources", "kind": "sources",
            "title": "Connect GitHub or another proof source",
            "detail": "Public repos, papers or posts raise the confidence of every skill they show.",
            "cta_label": "Connect", "cta_href": "/settings?tab=account",
        })

    visible = [t for t in todos if t["key"] not in dismissed]
    return visible[:MAX_TODOS]


def get_digest(session: Session, user_id: str, now: Optional[datetime] = None) -> dict:
    now = now or _utcnow()
    user = session.query(User).filter(User.id == user_id).first()
    profile = (user.profile_data if user else None) or {}
    dismissed = {k: v for k, v in (profile.get("briefing_dismissed") or {}).items()
                 if (_parse(v) or now) > now - DISMISS_FOR}
    since, hours = record_visit(user, now)

    prefs = session.query(CareerPreferences.pref_metadata).filter(CareerPreferences.user_id == user_id).first()
    tone = ((prefs[0] if prefs else None) or {}).get("communication_style")
    evidence = _evidence_counts(session, user_id)
    has_scores = session.query(CareerScore.url).filter(CareerScore.user_id == user_id).first() is not None
    sources_connected = session.query(ConnectedAccount.id).filter(
        ConnectedAccount.user_id == user_id, ConnectedAccount.is_active.is_(True)).first() is not None

    return {
        "v": 2,
        "first_name": profile.get("first_name") or (user.first_name if user else None),
        "tone": tone if tone in TONES else "warm",
        "since": since.isoformat(),
        "hours_since_last_visit": round(hours, 1) if hours is not None else None,
        "headline": _headline(session, user_id),
        "changes": _changes(session, user_id, since),
        "todos": _todos(session, user_id, now, dismissed, has_scores, sources_connected, evidence["skill_count"]),
        "week": _week(session, user_id, now),
        "evidence": evidence,
        "has_scores": has_scores,
    }
