"""Scan pipeline: open jobs in `jobs` → the user's titles → score what changed → upsert.

Jobs come from board syncs (careeros/jobs/ingest.py), not from the scan itself.
A job is rescored only when its input hash changes: the posting's content, the
user's profile fingerprint, or SCORER_VERSION. Runs as a background job; progress
is polled from `scan_jobs`.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import sqlalchemy as sa

from careeros.db.connection import db
from careeros.jobs.domain.job import Job
from careeros.jobs.models.job import Job as JobRow
from careeros.identity.domain.skill import Skill, SkillLevel
from careeros.identity.domain.profile import UserProfile
from careeros.evidence.aggregation import aggregate_user_skills
from careeros.shared.background import BackgroundJob, JobStore

logger = logging.getLogger(__name__)

scan_jobs = JobStore()

DEFAULT_YEARS_EXPERIENCE = 2.0
ALL_TIME_HOURS = 99999
# Bump when scoring logic changes: every job is rescored on the next scan
SCORER_VERSION = "2"


def skill_level_for(confidence: float) -> SkillLevel:
    """Aggregated evidence confidence → the scorer's skill level."""
    if confidence >= 0.9:
        return SkillLevel.EXPERT
    if confidence >= 0.8:
        return SkillLevel.ADVANCED
    if confidence >= 0.65:
        return SkillLevel.INDEPENDENT
    return SkillLevel.WORKING


def build_profile_from_evidence(user_id: str) -> Optional[UserProfile]:
    """UserProfile for a web user from users + evidence_items (+ sponsorship preference)."""
    with db.session_scope() as s:
        row = s.execute(
            sa.text("SELECT profile_data, years_in_role, email FROM users WHERE id = :u"), {"u": user_id}
        ).fetchone()
        if not row:
            return None
        aggregated = aggregate_user_skills(user_id, s)
        if not aggregated:
            return None

        profile_data, years_in_role, email = row[0] or {}, row[1], row[2]
        name = " ".join(x for x in [profile_data.get("first_name"), profile_data.get("last_name")] if x) or "Candidate"
        # total_years lives in profile_data JSONB; years_in_role is the column fallback
        years = float(profile_data.get("total_years") or years_in_role or DEFAULT_YEARS_EXPERIENCE)
        profile = UserProfile(
            name=name,
            email=email or "",
            years_experience=years,
            skills=[Skill(a["skill_name"], skill_level_for(a["aggregated_confidence"])) for a in aggregated],
        )

        sponsorship = s.execute(
            sa.text("SELECT requires_sponsorship FROM career_preferences WHERE user_id = :u"), {"u": user_id}
        ).fetchone()
        if sponsorship is not None:
            profile.preferences.work_visa_required = bool(sponsorship[0])
        return profile


def load_profile(user_id: str) -> Optional[UserProfile]:
    """CLI-era user_settings profile if it has skills, else the web (evidence-based) profile."""
    from careeros.identity.profile_service import ProfileService

    try:
        profile = ProfileService(user_id=user_id).get_profile()
    except Exception as e:
        logger.info("No user_settings profile for %s (%s); using evidence", user_id, e)
        profile = None
    if profile is None or not getattr(profile, "skills", []):
        profile = build_profile_from_evidence(user_id)
    return profile


def profile_fingerprint(profile: UserProfile, prefs: dict) -> str:
    """Everything about the user that changes a score."""
    data = {
        "skills": sorted((sk.name.lower(), str(sk.level)) for sk in profile.skills),
        "years": profile.years_experience,
        "preferences": {k: str(v) for k, v in sorted(vars(profile.preferences).items())},
        "prefs": prefs,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def input_hash(row: JobRow, fingerprint: str) -> str:
    content = row.content_hash or hashlib.sha256(f"{row.title}{row.location}{row.description}".encode()).hexdigest()
    return hashlib.sha256(f"{SCORER_VERSION}:{content}:{fingerprint}".encode()).hexdigest()


def pick_changed(rows: list[JobRow], known: dict[str, Optional[str]], fingerprint: str,
                 limit: int) -> tuple[list[JobRow], dict[str, str], int]:
    """(rows to score — first `limit`, in order —, their input hashes, how many are unchanged)."""
    changed, hashes = [], {}
    for r in rows:
        h = input_hash(r, fingerprint)
        if known.get(r.url) != h:
            changed.append(r)
            hashes[r.url] = h
    picked = changed[:limit]
    return picked, {r.url: hashes[r.url] for r in picked}, len(rows) - len(changed)


def candidate_urls(session, user_id: str, hours: int) -> list[str]:
    """Open jobs matching the user's titles, newest first (titles only — cheap)."""
    from careeros.jobs.targeting import user_title_filter

    titles = user_title_filter(session, user_id)
    q = session.query(JobRow.url, JobRow.title).filter(JobRow.closed_at.is_(None))
    if hours < ALL_TIME_HOURS:
        q = q.filter(JobRow.discovered_at >= datetime.now(timezone.utc) - timedelta(hours=hours))
    rows = q.order_by(JobRow.discovered_at.desc().nullslast()).all()
    return [url for url, title in rows if titles.keeps(title or "")]


def to_scoring_input(rows: list[JobRow]) -> tuple[list[Job], dict[str, dict]]:
    """Stored job rows → (Job objects to score, per-URL metadata the Job type doesn't carry)."""
    jobs = [
        Job(
            id=r.url,
            title=r.title or "",
            company=r.company or "",
            description=r.description or r.full_description or "",
            url=r.url,
            location=r.location or "",
            remote=bool(r.remote),
            required_skills=r.required_skills or [],
            required_years=float(r.required_years or DEFAULT_YEARS_EXPERIENCE),
            salary_min=r.salary_min,
            salary_max=r.salary_max,
            salary_currency=r.salary_currency or "USD",
            company_size=r.company_size or "unknown",
            sponsors_visa=r.sponsors_visa,
            source=r.source or "unknown",
        )
        for r in rows
    ]
    meta = {
        r.url: {
            "title": r.title or "",
            "company": r.company or "",
            "location": r.location or "",
            "remote": bool(r.remote),
            "remote_region": r.remote_region,
            "sponsors_visa": r.sponsors_visa,
            "salary_min": r.salary_min,
            "salary_max": r.salary_max,
            "required_skills": r.required_skills or [],
            "source": r.ats or r.site or r.source or "unknown",
            "company_key": r.company_key,
            "application_url": r.application_url or r.url,
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
        }
        for r in rows
    }
    return jobs, meta


def run_scan(job: BackgroundJob, user_id: str, hours: int = ALL_TIME_HOURS, limit: int = 500) -> None:
    """Background task: pick → score what changed → upsert. Fills `job` with progress and a summary."""
    from careeros.jobs.repositories.career_score_repo import CareerScoreRepository
    from careeros.jobs.scoring_service import ScoringService

    try:
        job.update(status="profile", progress=10)
        job.log("Loading your profile…")
        profile = load_profile(user_id)
        if profile is None:
            job.update(status="failed", error="No profile found — complete onboarding first.")
            return
        job.log(f"✓ Profile: {len(profile.skills)} skills, {profile.years_experience}y")
        service = ScoringService(user_id=user_id)
        fingerprint = profile_fingerprint(profile, service.load_prefs())

        job.update(status="scanning", progress=30)
        job.log("Picking open jobs that match your roles…")
        with db.session_scope() as s:
            urls = candidate_urls(s, user_id, hours)
            known = CareerScoreRepository(s).input_hashes(user_id)
            loaded = []
            for i in range(0, len(urls), 500):
                loaded += s.query(JobRow).filter(JobRow.url.in_(urls[i:i + 500])).all()
            order = {u: i for i, u in enumerate(urls)}
            loaded.sort(key=lambda r: order[r.url])
            rows, hashes, unchanged = pick_changed(loaded, known, fingerprint, limit)
            s.expunge_all()
        job.log(f"✓ {len(urls)} matching open jobs · {len(rows)} to score · {unchanged} unchanged")

        job.update(status="scoring", progress=60)
        if rows:
            job.log("Scoring against your career graph…")
            jobs, meta = to_scoring_input(rows)
            result = service.run_pipeline(jobs, profile, semantic=False, job_meta=meta, input_hashes=hashes)
        else:
            result = {"total_jobs": 0, "scored": 0, "saved_to_db": 0, "apply": 0, "consider": 0, "skip": 0}
        result.update(matching=len(urls), unchanged=unchanged)

        job.update(status="completed", progress=100, result=result)
        job.log(
            f"✓ Done — {result.get('apply', 0)} APPLY · "
            f"{result.get('consider', 0)} CONSIDER · "
            f"{result.get('skip', 0)} SKIP"
        )
    except Exception as e:
        logger.exception("Scan failed for %s", user_id)
        job.fail(e)
