"""Companies as the job boards see them: open roles, hiring pace, what they ask for.

The list is the boards CareerOS reads (infra/config/companies.yaml), not a hand-kept
seed: every number comes from the `jobs` table and the board sync log, and the
user's own view (fitting roles, best score, skills they already show) from their
scores and evidence. Seed profiles (tier, HQ, interview notes) are added when a
company has one.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from careeros.companies.models.company import Company
from careeros.evidence.aggregation import aggregate_user_skills
from careeros.jobs.boards import load_boards
from careeros.jobs.models.board_run import JobBoardRun
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job
from careeros.knowledge.skill_names import canonical, key as skill_key

TOP_SKILLS = 6
WEEK = timedelta(days=7)


def hiring_trend(new_this_week: int, new_last_week: int) -> str:
    """spike / up / stable / down from postings first seen this week vs the week before."""
    if new_this_week >= 5 and new_this_week >= 2 * max(new_last_week, 1):
        return "spike"
    if new_this_week >= 3 and new_this_week > new_last_week * 1.25:
        return "up"
    if new_last_week >= 3 and new_this_week < new_last_week * 0.6:
        return "down"
    return "stable"


def job_skills(job: Job) -> list[str]:
    """Canonical required skills: Claude's reading of this version of the posting, else keywords."""
    facts = job.llm_facts if job.llm_facts and job.llm_facts_hash == job.content_hash else None
    raw = (facts or {}).get("required_skills") or job.required_skills or []
    out: dict[str, str] = {}
    for s in raw:
        if isinstance(s, str) and s.strip():
            name = canonical(s)
            out.setdefault(name.lower(), name)
    return list(out.values())


def user_skill_keys(session: Session, user_id: str) -> set[str]:
    return {skill_key(s["skill_name"]) for s in aggregate_user_skills(user_id, session)}


def _seed_profiles(session: Session) -> dict[str, Company]:
    return {c.name.lower(): c for c in session.query(Company).all()}


def _user_scores(session: Session, user_id: str) -> dict[str, CareerScore]:
    rows = (session.query(CareerScore).join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None)).all())
    return {s.url: s for s in rows}


def _is_match(score: Optional[CareerScore]) -> bool:
    rec = (score.recommendation or "").upper() if score else ""
    return rec.startswith("APPLY") or rec.startswith("CONSIDER")


def _summary(board, jobs: list[Job], all_recent: list[Job], scores: dict[str, CareerScore],
             have: set[str], run: Optional[JobBoardRun], seed: Optional[Company], now: datetime) -> dict:
    open_jobs = [j for j in jobs if j.closed_at is None]
    new_this = sum(1 for j in all_recent if j.discovered_at and j.discovered_at > now - WEEK)
    new_last = sum(1 for j in all_recent if j.discovered_at and now - 2 * WEEK < j.discovered_at <= now - WEEK)
    closed_this = sum(1 for j in all_recent if j.closed_at and j.closed_at > now - WEEK)
    mine = [scores[j.url] for j in open_jobs if j.url in scores]
    matches = [s for s in mine if _is_match(s)]
    strong = [s for s in matches if (s.recommendation or "").upper().startswith("APPLY")]
    asked = Counter(skill for j in open_jobs for skill in job_skills(j))
    top = [{"name": n, "jobs": c, "you_show": skill_key(n) in have} for n, c in asked.most_common(TOP_SKILLS)]
    remote = sum(1 for j in open_jobs if j.remote)
    return {
        "key": board.key,
        "name": board.name,
        "ats": board.ats,
        "open_roles": len(open_jobs),
        "new_this_week": new_this,
        "new_last_week": new_last,
        "closed_this_week": closed_this,
        "trend": hiring_trend(new_this, new_last),
        "your_matches": len(matches),
        "your_strong": len(strong),
        "best_score": round(max((s.career_score or 0) for s in mine)) if mine else None,
        "remote_share": round(remote / len(open_jobs), 2) if open_jobs else None,
        "top_skills": top,
        "skills_you_show": sum(1 for s in top if s["you_show"]),
        "last_synced_at": run.last_success_at.isoformat() if run and run.last_success_at else None,
        "sync_error": bool(run and run.last_error),
        "profile": ({
            "tier": seed.tier, "industry": seed.industry, "headquarters": seed.headquarters,
            "sponsors_visa": seed.sponsors_visa, "employee_count": seed.employee_count,
        } if seed else None),
    }


def company_directory(session: Session, user_id: str, now: Optional[datetime] = None) -> list[dict]:
    """Every board's company, the ones with roles for this user first."""
    now = now or datetime.now(timezone.utc)
    boards = load_boards().boards
    recent_or_open = (session.query(Job)
                      .filter(Job.company_key.isnot(None),
                              or_(Job.closed_at.is_(None), Job.closed_at > now - 2 * WEEK,
                                  Job.discovered_at > now - 2 * WEEK))
                      .all())
    by_company: dict[str, list[Job]] = defaultdict(list)
    for j in recent_or_open:
        by_company[j.company_key].append(j)
    runs = {r.company_key: r for r in session.query(JobBoardRun).all()}
    seeds = _seed_profiles(session)
    scores = _user_scores(session, user_id)
    have = user_skill_keys(session, user_id)

    out = [_summary(b, by_company.get(b.key, []), by_company.get(b.key, []), scores, have,
                    runs.get(b.key), seeds.get(b.name.lower()), now) for b in boards]
    out.sort(key=lambda c: (-c["your_strong"], -c["your_matches"], -c["new_this_week"], -c["open_roles"], c["name"]))
    return out


WEEKS = 8


def weekly_new(session: Session, company_key: str, now: datetime, weeks: int = WEEKS) -> list[int]:
    """Postings first seen per week, oldest first (the last item is the current week)."""
    seen = [d for (d,) in session.query(Job.discovered_at).filter(
        Job.company_key == company_key, Job.discovered_at > now - weeks * WEEK).all() if d]
    counts = [0] * weeks
    for d in seen:
        age = int((now - d) / WEEK)
        if 0 <= age < weeks:
            counts[weeks - 1 - age] += 1
    return counts


def company_detail(session: Session, user_id: str, company_key: str, now: Optional[datetime] = None) -> Optional[dict]:
    """One company: the directory summary plus its open roles, best fit for this user first."""
    now = now or datetime.now(timezone.utc)
    board = next((b for b in load_boards().boards if b.key == company_key), None)
    if board is None:
        return None
    jobs = session.query(Job).filter(Job.company_key == company_key,
                                     or_(Job.closed_at.is_(None), Job.closed_at > now - 2 * WEEK,
                                         Job.discovered_at > now - 2 * WEEK)).all()
    scores = _user_scores(session, user_id)
    have = user_skill_keys(session, user_id)
    run = session.get(JobBoardRun, company_key)
    seed = _seed_profiles(session).get(board.name.lower())
    summary = _summary(board, jobs, jobs, scores, have, run, seed, now)

    roles = []
    for j in (j for j in jobs if j.closed_at is None):
        s = scores.get(j.url)
        roles.append({
            "url": j.url,
            "title": j.title,
            "location": j.location,
            "remote": bool(j.remote),
            "posted_at": (j.posted_at or j.discovered_at).isoformat() if (j.posted_at or j.discovered_at) else None,
            "score": round(s.career_score) if s and s.career_score is not None else None,
            "recommendation": (s.recommendation or "").split(" - ")[0].upper() if s else None,
            "application_url": j.application_url or j.url,
            "skills": job_skills(j)[:6],
        })
    roles.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0), r["title"]))
    summary["roles"] = roles
    summary["weekly_new"] = weekly_new(session, company_key, now)
    if seed:
        summary["profile"].update({
            "salary_ranges": seed.salary_ranges, "interview_rounds": seed.interview_rounds,
            "culture_signals": seed.culture_signals,
        })
    return summary
