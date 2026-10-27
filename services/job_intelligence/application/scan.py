"""Scan pipeline: job source → canonical jobs → score against the user's profile → save.

Runs as a background job; progress is polled from `scan_jobs`.
"""

import logging
from typing import Any, Optional

import sqlalchemy as sa

from core.db.connection import db
from core.domain import Job, Skill, SkillLevel, UserProfile
from services.evidence.aggregation import aggregate_user_skills
from shared.background import BackgroundJob, JobStore

logger = logging.getLogger(__name__)

scan_jobs = JobStore()

# Job source rows below this ApplyPilot fit score are not worth scoring
SOURCE_MIN_FIT_SCORE = 5
DEFAULT_YEARS_EXPERIENCE = 2.0


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
            sa.text("SELECT profile_data, years_in_role, email FROM users WHERE clerk_id = :u"), {"u": user_id}
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
    from services.identity_service.application.profile_service import ProfileService

    try:
        profile = ProfileService(user_id=user_id).get_profile()
    except Exception as e:
        logger.info("No user_settings profile for %s (%s); using evidence", user_id, e)
        profile = None
    if profile is None or not getattr(profile, "skills", []):
        profile = build_profile_from_evidence(user_id)
    return profile


def to_scoring_input(raw_jobs: list[dict], limit: int) -> tuple[list[Job], dict[str, dict]]:
    """Normalized source rows → (Job objects to score, per-URL metadata the Job type doesn't carry)."""
    rows = raw_jobs[:limit]
    jobs = [
        Job(
            id=j["url"],
            title=j.get("title", ""),
            company=j.get("company", ""),
            description=j.get("description", ""),
            url=j["url"],
            location=j.get("location", ""),
            remote=j.get("remote", False),
            required_skills=j.get("required_skills", []),
            required_years=float(j.get("required_years", DEFAULT_YEARS_EXPERIENCE)),
        )
        for j in rows
    ]
    meta = {
        j["url"]: {
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "remote": j.get("remote", False),
            "remote_region": j.get("remote_region"),
            "sponsors_visa": j.get("sponsors_visa", False),
            "salary_min": j.get("salary_min"),
            "salary_max": j.get("salary_max"),
            "required_skills": j.get("required_skills", []),
            "source": j.get("source", "unknown"),
        }
        for j in rows
    }
    return jobs, meta


def run_scan(job: BackgroundJob, user_id: str, hours: int, limit: int, source: str = "applypilot") -> None:
    """Background task: scan → score → save. Fills `job` with progress, logs and the summary."""
    from plugins.plugin_loader import load_job_source_plugin
    from .scoring_service import ScoringService

    try:
        job.update(status="profile", progress=10)
        job.log("Loading your profile…")
        profile = load_profile(user_id)
        if profile is None:
            job.update(status="failed", error="No profile found — complete onboarding first.")
            return
        job.log(f"✓ Profile: {len(profile.skills)} skills, {profile.years_experience}y")

        job.update(status="scanning", progress=30)
        job.log("Scanning job sources…")
        raw_jobs: list[dict[str, Any]] = load_job_source_plugin(source).scan_and_normalize(
            hours_old=hours, min_score=SOURCE_MIN_FIT_SCORE
        )
        job.log(f"✓ {len(raw_jobs)} jobs found (last {hours}h)")

        job.update(status="scoring", progress=60)
        job.log("Scoring against your career graph…")
        jobs, meta = to_scoring_input(raw_jobs, limit)
        result = ScoringService(user_id=user_id).run_pipeline(jobs, profile, semantic=False, job_meta=meta)

        job.update(status="completed", progress=100, result=result)
        job.log(
            f"✓ Done — {result.get('apply', 0)} APPLY · "
            f"{result.get('consider', 0)} CONSIDER · "
            f"{result.get('skip', 0)} SKIP"
        )
    except Exception as e:
        logger.exception("Scan failed for %s", user_id)
        job.fail(e)
