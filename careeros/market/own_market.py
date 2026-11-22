"""The market as the user's own job corpus shows it.

Read from the postings that match the user's roles (title filter, same as scoring):
how many are open and how fast new ones arrive, what they pay, how many are remote
or sponsor visas, which skills they ask for and whether that share is rising — set
against the user's evidence and the gaps in their matches. HN / TechCrunch signals
stay as the "news" layer (careeros/market/refresh.py).
"""

import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session, load_only

from careeros.companies.directory import job_skills, user_skill_keys
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job
from careeros.jobs.targeting import user_title_filter
from careeros.knowledge.skill_names import key as skill_key

TOP_SKILLS = 15
TOP_COMPANIES = 6
MIN_FOR_SHARE = 5   # below this many postings in a period, a share change is noise

_COLUMNS = (Job.url, Job.title, Job.company, Job.company_key, Job.remote, Job.sponsors_visa, Job.salary_min,
            Job.salary_currency, Job.required_skills, Job.llm_facts, Job.llm_facts_hash, Job.content_hash,
            Job.discovered_at, Job.closed_at)


def _pct_change(now: int, before: int) -> Optional[int]:
    if before <= 0:
        return None
    return round((now - before) / before * 100)


def market_snapshot(session: Session, user_id: str, days: int = 30, now: Optional[datetime] = None) -> dict:
    now = now or datetime.now(timezone.utc)
    period = timedelta(days=days)
    titles = user_title_filter(session, user_id)

    def mine(q):
        return [j for j in q.options(load_only(*_COLUMNS)).all() if titles.keeps(j.title or "")]

    open_jobs = mine(session.query(Job).filter(Job.closed_at.is_(None)))
    recent = mine(session.query(Job).filter(Job.discovered_at > now - 2 * period))
    this = [j for j in recent if j.discovered_at > now - period]
    before = [j for j in recent if j.discovered_at <= now - period]

    # Pay: the most common currency among postings that state a salary
    paid = [j for j in open_jobs if j.salary_min]
    currency = Counter((j.salary_currency or "USD") for j in paid).most_common(1)
    cur = currency[0][0] if currency else None
    amounts = sorted(j.salary_min for j in paid if (j.salary_currency or "USD") == cur)

    visa_stated = [j for j in open_jobs if j.sponsors_visa is not None]

    # Skills: share of open matching postings asking for each, and how that share moved
    have = user_skill_keys(session, user_id)
    open_count = Counter(s for j in open_jobs for s in job_skills(j))
    this_count = Counter(s for j in this for s in job_skills(j))
    before_count = Counter(s for j in before for s in job_skills(j))
    gaps = Counter()
    for (g,) in session.query(CareerScore.skill_gaps).filter(CareerScore.user_id == user_id).all():
        for s in g or []:
            gaps[skill_key(str(s))] += 1

    skills = []
    for name, n in open_count.most_common(TOP_SKILLS):
        share_now = this_count[name] / len(this) if len(this) >= MIN_FOR_SHARE else None
        share_before = before_count[name] / len(before) if len(before) >= MIN_FOR_SHARE else None
        skills.append({
            "name": name,
            "open_jobs": n,
            "share": round(n / len(open_jobs), 3) if open_jobs else 0,
            "trend_pts": (round((share_now - share_before) * 100, 1)
                          if share_now is not None and share_before is not None else None),
            "you_show": skill_key(name) in have,
            "missing_in_your_matches": gaps.get(skill_key(name), 0),
        })

    companies = Counter((j.company_key, j.company) for j in this if j.company)
    return {
        "days": days,
        "open_matches": len(open_jobs),
        "new_this_period": len(this),
        "new_last_period": len(before),
        "change_pct": _pct_change(len(this), len(before)),
        "salary": ({"currency": cur, "median": int(statistics.median(amounts)), "low": amounts[len(amounts) // 4],
                    "high": amounts[(len(amounts) * 3) // 4], "postings": len(amounts)} if amounts else None),
        "salary_stated_share": round(len(paid) / len(open_jobs), 2) if open_jobs else None,
        "remote_share": round(sum(1 for j in open_jobs if j.remote) / len(open_jobs), 2) if open_jobs else None,
        "visa": ({"sponsor_share": round(sum(1 for j in visa_stated if j.sponsors_visa) / len(visa_stated), 2),
                  "stated": len(visa_stated)} if visa_stated else None),
        "skills": skills,
        "busiest_companies": [{"key": k, "name": n, "new": c} for (k, n), c in companies.most_common(TOP_COMPANIES)],
    }
