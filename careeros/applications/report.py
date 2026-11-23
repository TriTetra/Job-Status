"""The daily report: what you sent, where each stands and what its chance is now, what's ready
to send today, and the one skill that would open the most doors.

A silent application isn't a rejection: most employer replies come within days, so the chance
falls as the silence grows (P(answer | t days silent) = p(1-F(t)) / (1-p·F(t)), F = the share
of replies that arrive within t days). After 21 days it's probably ghosted, after 45 closed.
"""

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job

# Reply delay: median about 6 days, three in four within about 15 (Huntr 2025, self-reported)
REPLY_MEDIAN_DAYS = 6.0
REPLY_SIGMA = 1.36
GHOSTED_AFTER_DAYS = 21
CLOSED_AFTER_DAYS = 45
ACTIVE = ("applied", "interview", "offer")
MIN_GAP_JOBS = 3


def replied_by(days: float) -> float:
    """Share of eventual replies that have arrived after `days` days (log-normal)."""
    if days <= 0:
        return 0.0
    z = (math.log(days) - math.log(REPLY_MEDIAN_DAYS)) / (REPLY_SIGMA * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))


def chance_after_silence(p: float, days: float) -> float:
    """Chance an application still gets an answer, given `days` of silence."""
    f = replied_by(days)
    denom = 1 - p * f
    return p * (1 - f) / denom if denom > 0 else 0.0


def waiting_label(days: Optional[int]) -> str:
    if days is None:
        return "waiting"
    if days >= CLOSED_AFTER_DAYS:
        return "closed (no answer)"
    if days >= GHOSTED_AFTER_DAYS:
        return "probably ghosted"
    if days >= 14:
        return "follow up"
    return "waiting"


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def daily_report(session: Session, user_id: str, now: Optional[datetime] = None) -> dict:
    from careeros.applications.pipeline import pipeline
    from careeros.applications.queue import today as queue_today

    now = now or datetime.now(timezone.utc)
    apps = pipeline(session, user_id, now)
    urls = [a["url"] for a in apps]
    scores = {s.url: s for s in session.query(CareerScore).filter(CareerScore.user_id == user_id,
                                                                  CareerScore.url.in_(urls)).all()} if urls else {}

    active = []
    for a in apps:
        if a["status"] not in ACTIVE:
            continue
        s = scores.get(a["url"])
        ex = (s.explanation or {}) if s else {}
        p = ((ex.get("model") or {}).get("p_effective"))
        applied = _aware(datetime.fromisoformat(a["applied_at"])) if a.get("applied_at") else None
        silent = (now - applied).days if applied and a["status"] == "applied" else a.get("days_in_status")
        item = {
            "url": a["url"], "title": a["title"], "company": a["company"], "company_key": a.get("company_key"),
            "status": a["status"], "days": silent, "posting_closed": a.get("posting_closed"),
            "trust": ex.get("trust"),
        }
        if a["status"] == "applied":
            item["state"] = waiting_label(silent)
            if isinstance(p, (int, float)):
                item["chance_now"] = round(chance_after_silence(p, silent or 0), 4)
                item["chance_at_send"] = round(p, 4)
        else:
            item["state"] = {"interview": "interviewing", "offer": "offer"}[a["status"]]
        active.append(item)

    week_ago = now - timedelta(days=7)
    sent_week = sum(1 for a in apps if a.get("applied_at") and _aware(datetime.fromisoformat(a["applied_at"])) >= week_ago)
    counts = Counter(a["status"] for a in apps)

    queue = queue_today(session, user_id, now=now)

    # the skill missing from the most of your good open matches
    gaps = Counter()
    rows = (session.query(CareerScore.skill_gaps, CareerScore.recommendation).join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None)).all())
    for g, rec in rows:
        if (rec or "").upper().startswith(("APPLY", "CONSIDER")):
            gaps.update(str(x) for x in (g or []))
    learn = [{"skill": k, "jobs": n} for k, n in gaps.most_common(3) if n >= MIN_GAP_JOBS]

    since = now - timedelta(days=1)
    new_matches = (session.query(CareerScore.recommendation).join(Job, Job.url == CareerScore.url)
                   .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None),
                           Job.discovered_at >= since).all())
    new_good = sum(1 for (rec,) in new_matches if (rec or "").upper().startswith(("APPLY", "CONSIDER")))

    return {
        "date": now.date().isoformat(),
        "sent_this_week": sent_week,
        "counts": {k: counts.get(k, 0) for k in ("to_apply", "applied", "interview", "offer", "rejected")},
        "active": active,
        "ghosted": sum(1 for a in active if a.get("state") in ("probably ghosted", "closed (no answer)")),
        "queue": [{k: q[k] for k in ("url", "title", "company", "score", "p_interview", "ready")} for q in queue],
        "learn": learn,
        "new_matches": len(new_matches),
        "new_good_matches": new_good,
    }


def report_text(r: dict, app_url: str) -> str:
    """The report as a short Telegram message (HTML)."""
    import html

    def e(x) -> str:
        return html.escape(str(x or ""), quote=False)

    lines = [f"📋 <b>Your day, {e(r['date'])}</b>"]
    q = r["queue"]
    if q:
        lines.append(f"\n<b>{len(q)} ready to apply</b>")
        lines += [f"• {e(x['title'])} · {e(x['company'])} · {round(x['score'] or 0)}" for x in q[:5]]
        lines.append(f"<a href=\"{e(app_url + '/apply')}\">Open the queue</a>")
    if r["active"]:
        lines.append(f"\n<b>Waiting on {len(r['active'])}</b> · sent this week: {r['sent_this_week']}")
        for a in r["active"][:6]:
            chance = f" · {a['chance_now'] * 100:.1f}% chance of an answer" if a.get("chance_now") is not None else ""
            lines.append(f"• {e(a['company'])}: {e(a['state'])}, {a['days'] if a['days'] is not None else '?'} days{chance}")
    if r["learn"]:
        top = r["learn"][0]
        lines.append(f"\n<b>Learn next:</b> {e(top['skill'])}: missing in {top['jobs']} of your good matches")
    if r["new_good_matches"]:
        lines.append(f"\n{r['new_good_matches']} new good match{'es' if r['new_good_matches'] != 1 else ''} in the last day")
    return "\n".join(lines)
