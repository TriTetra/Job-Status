"""Jobs router — real opportunities + scan pipeline (no mocks)."""
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from ..schemas.job import JobListResponse, JobWithScore
from core.db.models.career_score import CareerScore
from core.db.models.application import Application
from core.db.repositories import CareerScoreRepository
from core.db.repositories.career_preferences_repo import CareerPreferencesRepository
from services.job_intelligence.application.decision_builder import build_decision, reasoning_for

router = APIRouter()

# In-memory scan job store (production'da Redis kullanılır)
scan_jobs: dict[str, dict] = {}

# User decision status mapping
_STATUS_MAP = {
    "to_apply": "shortlisted",
    "applied": "applied",
    "interview": "interviewing",
    "offer": "offer",
    "skipped": "skipped",
    "rejected": "skipped",
    "withdrawn": "skipped",
}


def _user_decision_map(session: Session, user_id: str) -> Dict[str, dict]:
    """Fetch all applications for user, return {url: {status, decided_at}} map."""
    rows = (
        session.query(Application.url, Application.status, Application.updated_at)
        .filter(Application.user_id == user_id)
        .all()
    )
    return {
        url: {
            "status": _STATUS_MAP.get(st, "skipped"),
            "decided_at": ua.isoformat() if ua else None,
        }
        for url, st, ua in rows
    }


def _serialize(s: CareerScore, user_decision: Optional[dict] = None) -> JobWithScore:
    rec = (s.recommendation or "CONSIDER").split(" - ")[0].strip().upper()
    if rec not in ("APPLY", "CONSIDER", "SKIP"):
        rec = "CONSIDER"
    return JobWithScore(
        url=s.url,
        career_score=s.career_score,
        fit_score=s.fit_score,
        acceptance_probability=s.acceptance_probability,
        career_value=s.career_value,
        market_demand=s.market_demand,
        expected_value=s.expected_value,
        recommendation=rec,
        skill_gaps=s.skill_gaps or [],
        explanation=s.explanation or {},
        scanned_at=s.scanned_at.isoformat() if s.scanned_at else None,
        user_decision=user_decision or {"status": "unreviewed", "decided_at": None},
    )


@router.get("/", response_model=JobListResponse)
def list_jobs(
    recommendation: str = Query("ALL", description="APPLY | CONSIDER | SKIP | ALL"),
    limit: int = Query(200, le=500, description="Max opportunities to return"),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """
    Return ALL scored opportunities (no min_score filter).
    
    Scoring classifies opportunities; it does not hide them.
    The frontend will group by tier (strong/look/low) and present
    all tiers to the user, with low fit collapsed by default.
    """
    repo = CareerScoreRepository(session)
    dmap = _user_decision_map(session, user_id)
    
    if recommendation != "ALL":
        scores = repo.get_top_opportunities(
            min_score=0.0,  # No threshold — return all
            recommendation=recommendation,
            limit=limit,
            user_id=user_id,
        )
    else:
        # Get latest score per URL, sorted by career_score desc
        latest = (
            select(CareerScore.url, func.max(CareerScore.scanned_at).label("latest_scan"))
            .where(CareerScore.user_id == user_id)
            .group_by(CareerScore.url)
            .subquery()
        )
        stmt = (
            select(CareerScore)
            .join(
                latest,
                and_(
                    CareerScore.url == latest.c.url,
                    CareerScore.scanned_at == latest.c.latest_scan,
                ),
            )
            .where(CareerScore.user_id == user_id)
            .order_by(CareerScore.career_score.desc())
            .limit(limit)
        )
        scores = list(session.execute(stmt).scalars().all())
    
    return JobListResponse(
        total=len(scores),
        jobs=[_serialize(s, dmap.get(s.url)) for s in scores]
    )


@router.get("/pipeline", summary="Pipeline summary counts")
def pipeline_counts(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Return counts per recommendation bucket."""
    from core.db.repositories import ApplicationRepository
    repo = ApplicationRepository(session)
    return repo.get_pipeline_summary(user_id=user_id)


@router.get("/reasoning/{url:path}")
def get_reasoning(
    url: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """
    On-demand reasoning: LLM first, template fallback.
    Caches result in explanation.decision.reasoning.
    """
    score = CareerScoreRepository(session).get_latest_score(url=url, user_id=user_id)
    if not score:
        raise HTTPException(status_code=404, detail="Job not found")

    ex = dict(score.explanation or {})
    dec = ex.get("decision")
    
    # Build decision if missing (old rows before Contract v1)
    if not dec:
        p = CareerPreferencesRepository(session).get_by_user_id(user_id)
        prefs = {
            "work_arrangements": p.work_arrangements or [],
            "preferred_country_codes": p.preferred_country_codes or [],
            "requires_sponsorship": p.requires_sponsorship,
            "salary_min": p.salary_min,
            "salary_max": p.salary_max,
        } if p else {}
        
        dec = build_decision(
            recommendation=score.recommendation,
            career_score=score.career_score or 0,
            career_value=score.career_value or 0,
            market_demand=score.market_demand or 0,
            job=ex,
            prefs=prefs,
            matched_skills=ex.get("matched_skills") or [],
            gap_skills=score.skill_gaps or [],
        )

    # Generate reasoning if missing
    if not dec.get("reasoning"):
        text, src = reasoning_for(ex, dec, ex.get("matched_skills") or [], score.skill_gaps or [])
        dec["reasoning"] = text
        dec["reasoning_source"] = src
        dec["generated_at"] = datetime.utcnow().isoformat()
        ex["decision"] = dec
        score.explanation = ex
        session.commit()

    return {"decision": dec}


# ─── Scan pipeline ───────────────────────────────────────────────────────────

def _build_profile_from_evidence(user_id: str):
    """
    Web users live in users/evidence_items — build UserProfile from evidence.
    Fallback when ProfileService cannot find a user_settings row.
    """
    import sqlalchemy as sa
    from core.db.connection import db as _db
    from core.domain import Skill, SkillLevel, UserProfile
    from ..core.evidence.confidence_aggregator import aggregate_user_skills  # noqa: F401

    try:
        from app.core.evidence.confidence_aggregator import aggregate_user_skills
    except ImportError:
        return None

    with _db.session_scope() as s:
        # FIX: total_years is NOT a column — it lives inside profile_data JSONB
        row = s.execute(
            sa.text(
                "SELECT profile_data, years_in_role, email "
                "FROM users WHERE clerk_id = :u"
            ),
            {"u": user_id},
        ).fetchone()
        if not row:
            return None

        pd = row[0] or {}
        agg = aggregate_user_skills(user_id, s)
        if not agg:
            return None

        skills = []
        for a in agg:
            c = a["aggregated_confidence"]
            if c >= 0.9:
                level = SkillLevel.EXPERT
            elif c >= 0.8:
                level = SkillLevel.ADVANCED
            elif c >= 0.65:
                level = SkillLevel.INDEPENDENT
            else:
                level = SkillLevel.WORKING
            skills.append(Skill(a["skill_name"], level))

        name = " ".join(x for x in [pd.get("first_name"), pd.get("last_name")] if x) or "Candidate"
        # total_years comes from JSONB, years_in_role is the DB column fallback
        years = float(pd.get("total_years") or row[1] or 2)
        profile = UserProfile(name=name, email=row[2] or "", years_experience=years, skills=skills)

        try:
            prefs = s.execute(
                sa.text(
                    "SELECT requires_sponsorship FROM career_preferences WHERE user_id = :u"
                ),
                {"u": user_id},
            ).fetchone()
            if prefs is not None:
                profile.preferences.work_visa_required = bool(prefs[0])
        except Exception:
            pass

        return profile


def run_scan(job_id: str, user_id: str, hours: int, limit: int) -> None:
    job = scan_jobs[job_id]

    def log(msg: str) -> None:
        job["logs"].append({"timestamp": datetime.utcnow().isoformat(), "message": msg})

    try:
        job.update(status="profile", progress=10)
        log("Loading your profile…")

        from services.identity_service.application.profile_service import ProfileService

        profile = None
        try:
            profile = ProfileService(user_id=user_id).get_profile()
        except Exception:
            profile = None

        if profile is None or not getattr(profile, "skills", []):
            profile = _build_profile_from_evidence(user_id)

        if profile is None:
            job.update(status="failed", error="No profile found — complete onboarding first.")
            return

        log(f"✓ Profile: {len(profile.skills)} skills, {profile.years_experience}y")

        job.update(status="scanning", progress=30)
        log("Scanning job sources…")

        from plugins.plugin_loader import load_job_source_plugin
        from core.domain import Job

        raw_jobs = load_job_source_plugin("applypilot").scan_and_normalize(
            hours_old=hours, min_score=5  # lowered from 7 — captures score 5-6 jobs too
        )
        log(f"✓ {len(raw_jobs)} jobs found (last {hours}h)")

        # Build job_dicts mapping for decision builder
        job_dicts = {
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
            for j in raw_jobs[:limit]
        }

        jobs_to_score = [
            Job(
                id=j["url"],
                title=j.get("title", ""),
                company=j.get("company", ""),
                description=j.get("description", ""),
                url=j["url"],
                location=j.get("location", ""),
                remote=j.get("remote", False),
                required_skills=j.get("required_skills", []),
                required_years=float(j.get("required_years", 2.0)),
            )
            for j in raw_jobs[:limit]
        ]

        job.update(status="scoring", progress=60)
        log("Scoring against your career graph…")

        from services.job_intelligence.application.scoring_service import ScoringService

        result = ScoringService(user_id=user_id).run_pipeline(
            jobs_to_score, profile, semantic=False, job_dicts=job_dicts
        )

        job.update(status="completed", progress=100, result=result)
        log(
            f"✓ Done — {result.get('apply', 0)} APPLY · "
            f"{result.get('consider', 0)} CONSIDER · "
            f"{result.get('skip', 0)} SKIP"
        )

    except Exception as e:
        job.update(status="failed", error=str(e))
        log(f"✗ {e}")


@router.post("/scan")
def start_scan(
    background_tasks: BackgroundTasks,
    hours: int = Query(99999, ge=0, le=99999, description="Hours to look back (0=all time)"),
    limit: int = Query(200, ge=1, le=500),
    user_id: str = Depends(get_user_id),
):
    """
    Start a background scan → score → save run.
    Poll GET /scan/{job_id}/status for progress.
    """
    job_id = str(uuid.uuid4())
    scan_jobs[job_id] = {
        "job_id": job_id,
        "user_id": user_id,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "result": None,
        "error": None,
    }
    background_tasks.add_task(run_scan, job_id, user_id, hours, limit)
    return {"job_id": job_id, "status": "pending"}


@router.get("/scan/{job_id}/status")
def scan_status(job_id: str, user_id: str = Depends(get_user_id)):
    """Poll scan progress and logs."""
    job = scan_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["user_id"] != user_id:
        raise HTTPException(403, "Unauthorized")
    return job


@router.get("/{url:path}", response_model=JobWithScore)
def get_job(
    url: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Latest score for a specific job URL."""
    score = CareerScoreRepository(session).get_latest_score(url=url, user_id=user_id)
    if not score:
        raise HTTPException(status_code=404, detail="Job not found")
    
    dmap = _user_decision_map(session, user_id)
    return _serialize(score, dmap.get(score.url))
