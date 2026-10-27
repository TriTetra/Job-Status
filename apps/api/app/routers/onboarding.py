"""Onboarding API — state machine + profile data persistence."""

from typing import Optional, List
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from core.domain.identity.onboarding import OnboardingState
from core.db.repositories.user_repo import UserRepository

router = APIRouter()

# In-memory job store (production'da Redis kullan)
extraction_jobs: dict[str, "ExtractionJob"] = {}

class ExtractionJob:
    def __init__(self, job_id: str, user_id: str, filename: str):
        self.job_id = job_id
        self.user_id = user_id
        self.filename = filename
        self.status = "pending"  # pending | parsing | extracting | completed | failed
        self.progress = 0
        self.logs: list[dict] = []
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()

    def add_log(self, message: str, type: str = "info"):
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "type": type
        })

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat()
        }



class GraphNode(BaseModel):
    id: str
    type: str  # "skill" | "project" | "company" | "evidence"
    label: str
    confidence: float = 1.0
    metadata: dict = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0

class CareerGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: dict


# ─── Request/Response schemas ─────────────────────────────────────────────────

class IdentityPayload(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    current_role_id: str = Field(..., min_length=1, max_length=200)
    current_role_title: str = Field(..., min_length=1, max_length=150)
    years_in_role: float = Field(..., ge=0, le=50)
    career_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|expert)$")
    career_level_origin: str = Field("system", pattern="^(user|system|ai_estimated)$")
    country: str = Field(..., min_length=1, max_length=100)
    total_years: Optional[float] = Field(None, ge=0, le=50)
    languages: list[dict] = Field(default_factory=list)        # [{"code":"English","level":"C1"}]
    education_level: Optional[str] = Field(None, pattern="^(none|bachelor|master|phd)$")


class GoalsPayload(BaseModel):
    goal_ids: list[str] = Field(..., min_length=1, max_length=5)
    preferred_role_ids: list[str] = Field(..., min_length=1, max_length=5)
    preferred_country_codes: list[str] = Field(..., min_length=1, max_length=5)
    work_arrangements: list[str] = Field(default_factory=list, max_length=3)
    requires_sponsorship: Optional[bool] = Field(None)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    salary_period: str = Field("year", pattern="^(year|month|hour|day|project)$")
    salary_negotiable: bool = Field(True)
    contract_types: list[str] = Field(default_factory=list, max_length=4)
    availability: Optional[str] = Field(None, pattern="^(immediately|2_weeks|1_month|3_months_plus)$")
    target_seniority: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|expert)$")


class OnboardingStateOut(BaseModel):
    state: str
    profile_data: dict
    preferences: Optional[dict] = None
    next_step: Optional[str]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_user(repo: UserRepository, clerk_id: str):
    user = repo.get_by_clerk_id(clerk_id)
    if not user:
        user = repo.upsert_from_clerk(
            clerk_id=clerk_id,
            email=f"{clerk_id}@placeholder-applypilot.com",
            first_name="New",
            last_name="User",
        )
        repo.session.commit()
    return user


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/state", response_model=OnboardingStateOut)
def get_onboarding_state(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    from core.db.repositories.career_preferences_repo import CareerPreferencesRepository

    repo = UserRepository(session)
    user = _require_user(repo, user_id)

    prefs_repo = CareerPreferencesRepository(session)
    prefs = prefs_repo.get_by_user_id(user_id)

    preferences = None
    if prefs:
        preferences = {
            "goal_ids": prefs.goal_ids or [],
            "preferred_role_ids": prefs.preferred_role_ids or [],
            "preferred_country_codes": prefs.preferred_country_codes or [],
            "work_arrangements": prefs.work_arrangements or [],
            "requires_sponsorship": prefs.requires_sponsorship,
            "contract_types": prefs.contract_types or [],
            "availability": prefs.availability,
            "target_seniority": prefs.target_seniority,
            "salary": {
                "min": prefs.salary_min,
                "max": prefs.salary_max,
                "currency": prefs.salary_currency,
                "period": prefs.salary_period,
                "negotiable": prefs.salary_negotiable,
            } if (prefs.salary_min is not None or prefs.salary_max is not None) else None,
        }

    return OnboardingStateOut(
        state=user.onboarding_state,
        profile_data=user.profile_data or {},
        preferences=preferences,
        next_step=OnboardingState.next_state(user.onboarding_state),
    )


@router.post("/identity")
def save_identity(
    data: IdentityPayload,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    import re
    from datetime import date
    import sqlalchemy as sa
    from core.db.models.custom_role import CustomRole

    repo = UserRepository(session)
    user = _require_user(repo, user_id)

    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    is_uuid = bool(UUID_PATTERN.match(data.current_role_id))
    is_custom_prefix = data.current_role_id.startswith('custom_')

    if is_uuid:
        # Direct UUID FK → canonical role
        canonical_uuid = data.current_role_id
        user.current_role_id = canonical_uuid
        user.current_custom_role_id = None
        source = 'canonical'
        role_id_for_history = canonical_uuid
        custom_role_id_for_history = None
    elif not is_custom_prefix:
        # Slug from static fallback → look up UUID in roles table
        role_row = session.execute(
            sa.text("SELECT id FROM roles WHERE slug = :slug LIMIT 1"),
            {'slug': data.current_role_id}
        ).fetchone()

        if role_row:
            canonical_uuid = str(role_row[0])
            user.current_role_id = canonical_uuid
            user.current_custom_role_id = None
            source = 'canonical'
            role_id_for_history = canonical_uuid
            custom_role_id_for_history = None
        else:
            # Unrecognized slug → treat as custom role
            is_custom_prefix = True

    if is_custom_prefix:
        # Upsert into custom_roles (idempotent: same user+title reuses existing)
        existing = session.execute(
            sa.text("SELECT id FROM custom_roles WHERE user_id = :uid AND title = :title LIMIT 1"),
            {'uid': user_id, 'title': data.current_role_title}
        ).fetchone()

        if existing:
            custom_id = str(existing[0])
        else:
            custom_role = CustomRole(
                id=uuid.uuid4(),
                user_id=user_id,
                title=data.current_role_title,
            )
            session.add(custom_role)
            session.flush()
            custom_id = str(custom_role.id)

        user.current_role_id = None
        user.current_custom_role_id = custom_id
        source = 'custom'
        role_id_for_history = None
        custom_role_id_for_history = custom_id

    # Career fields
    user.years_in_role = data.years_in_role
    user.career_level = data.career_level
    user.career_level_origin = data.career_level_origin

    # Profile data
    user.profile_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "country": data.country,
        "current_role_title": data.current_role_title,
        "total_years": data.total_years,
        "languages": data.languages,
        "education_level": data.education_level,
    }

    # End previous current role in history
    session.execute(
        sa.text("""
            UPDATE user_roles
            SET is_current = false, ended_at = :today
            WHERE user_id = :user_id AND is_current = true
        """),
        {'user_id': user_id, 'today': date.today()}
    )

    # Insert new current role
    session.execute(
        sa.text("""
            INSERT INTO user_roles (id, user_id, role_id, custom_role_id, started_at, is_current, source)
            VALUES (:id, :user_id, :role_id, :custom_role_id, :started_at, true, :source)
        """),
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'role_id': role_id_for_history,
            'custom_role_id': custom_role_id_for_history,
            'started_at': date.today(),
            'source': source,
        }
    )

    # Advance state machine
    if user.onboarding_state in (OnboardingState.NOT_STARTED.value, OnboardingState.IDENTITY.value):
        user.onboarding_state = OnboardingState.GOALS.value

    session.commit()

    return {"state": user.onboarding_state, "message": "Identity saved"}


@router.post("/goals")
def save_goals(
    data: GoalsPayload,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    from core.db.repositories.career_preferences_repo import CareerPreferencesRepository

    if data.salary_min is not None and data.salary_max is not None:
        if data.salary_min > data.salary_max:
            raise HTTPException(
                status_code=400,
                detail="salary_min cannot be greater than salary_max",
            )

    prefs_repo = CareerPreferencesRepository(session)
    prefs_repo.upsert(
        user_id=user_id,
        goal_ids=data.goal_ids,
        preferred_role_ids=data.preferred_role_ids,
        preferred_country_codes=data.preferred_country_codes,
        work_arrangements=data.work_arrangements,
        requires_sponsorship=data.requires_sponsorship,
        contract_types=data.contract_types,
        availability=data.availability,
        target_seniority=data.target_seniority,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        salary_currency=data.salary_currency,
        salary_period=data.salary_period,
        salary_negotiable=data.salary_negotiable,
    )

    repo = UserRepository(session)
    user = _require_user(repo, user_id)
    if user.onboarding_state == OnboardingState.GOALS.value:
        user.onboarding_state = OnboardingState.EVIDENCE.value

    session.commit()
    return {"state": user.onboarding_state, "message": "Goals saved"}


@router.post("/advance")
def advance_state(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Manually advance to next state (EVIDENCE → CONNECTIONS → BUILDING → READY)."""
    repo = UserRepository(session)
    user = _require_user(repo, user_id)

    nxt = OnboardingState.next_state(user.onboarding_state)
    if nxt:
        user.onboarding_state = nxt

    return {"state": user.onboarding_state}


@router.post("/complete")
def complete_onboarding(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    repo = UserRepository(session)
    user = _require_user(repo, user_id)
    user.onboarding_state = OnboardingState.READY.value
    return {"state": user.onboarding_state, "message": "Onboarding complete"}


@router.post("/resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Upload resume PDF and start extraction job."""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    job = ExtractionJob(job_id, user_id, file.filename)
    extraction_jobs[job_id] = job
    
    # Save file temporarily in personal/ (workspace-relative, gitignored)
    import os
    os.makedirs("personal", exist_ok=True)
    file_path = f"personal/resume_{job_id}.pdf"
    with open(file_path, "wb") as f:
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="PDF too large — max 25 MB")
        f.write(content)
    
    # Start background extraction (new session — request session may close before BG task runs)
    background_tasks.add_task(run_extraction, job_id, file_path, user_id)

    return {"job_id": job_id, "status": "pending"}


def run_extraction(job_id: str, file_path: str, user_id: str):
    """Background task: real PDF → LLM → evidence items pipeline."""
    from core.db.connection import db as _db
    from core.db.models.resume_document import ResumeDocument
    from ..evidence.resume_pipeline import process_resume

    job = extraction_jobs[job_id]

    def log(msg: str):
        job.add_log(msg)

    try:
        with _db.session_scope() as bg_session:
            # Create ResumeDocument record
            resume_doc = ResumeDocument(
                user_id=user_id,
                filename=job.filename,
                storage_key=file_path,
                parse_status="pending",
            )
            bg_session.add(resume_doc)
            bg_session.commit()
            bg_session.refresh(resume_doc)

            job.status = "parsing"
            job.progress = 15

            # Run the pipeline (sync — runs in FastAPI thread pool via BackgroundTasks)
            summary = process_resume(resume_doc, bg_session, log=log)

            job.progress = 90
            job.add_log("Updating profile state...")

            # Advance onboarding state
            repo = UserRepository(bg_session)
            repo.set_onboarding_state(user_id, OnboardingState.CONNECTIONS)
            repo.patch_profile_data(user_id, {
                "resume_path": file_path,
                "resume_doc_id": resume_doc.id,
            })

            job.result = {
                "skills_extracted": summary["skills_count"],
                "experience_count": summary["experience_count"],
                "projects_count": summary["projects_count"],
                "evidence_items": (
                    summary["skills_count"]
                    + summary["experience_count"]
                    + summary["projects_count"]
                ),
            }
            job.progress = 100
            job.status = "completed"
            job.add_log("Extraction complete — Career Graph ready")

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.add_log(f"Extraction failed: {exc}", type="error")


@router.get("/resume/{job_id}/status")
async def get_extraction_status(
    job_id: str,
    user_id: str = Depends(get_user_id),
):
    """Poll extraction job status."""
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = extraction_jobs[job_id]
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return job.to_dict()


@router.post("/build-graph")
async def build_career_graph(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Build Career Graph from extracted evidence items."""
    repo = UserRepository(session)
    user = repo.get_by_clerk_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has evidence items
    from core.db.models.evidence_item import EvidenceItem
    evidence_count = session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id
    ).count()

    if evidence_count == 0:
        raise HTTPException(status_code=400, detail="No evidence items found. Upload resume first.")

    # Generate job ID
    job_id = str(uuid.uuid4())
    extraction_jobs[job_id] = ExtractionJob(job_id, user_id, "career_graph")

    # Start background graph building
    background_tasks.add_task(run_graph_building, job_id, user_id)

    return {"job_id": job_id, "status": "pending"}


def run_graph_building(job_id: str, user_id: str):
    """Background task: build Career Graph from actual database evidence items.

    Opens its own DB session — the request session may be closed by the time
    this runs. Sync function → FastAPI executes it in the thread pool,
    mirroring run_extraction (no event-loop blocking).
    """
    import time
    from core.db.connection import db as _db
    from core.db.models.evidence_item import EvidenceItem
    from core.db.models.career_graph_node import CareerGraphNode

    job = extraction_jobs[job_id]

    try:
        with _db.session_scope() as session:
            # Stage 1: Fetch evidence items
            job.status = "parsing"
            job.progress = 15
            job.add_log("📄 Fetching evidence items from database...", "info")
            time.sleep(1.0)

            evidence_items = session.query(EvidenceItem).filter(
                EvidenceItem.user_id == user_id
            ).all()

            if not evidence_items:
                raise ValueError("No evidence items found. Please upload your resume first.")

            skills = [e for e in evidence_items if (e.evidence_data or {}).get("type", "skill") == "skill"]
            selected_projects = [e for e in evidence_items if (e.evidence_data or {}).get("type") == "project"]
            selected_experiences = [e for e in evidence_items if (e.evidence_data or {}).get("type") == "experience"]
            achievements = [
                e for e in evidence_items
                if (e.evidence_data or {}).get("type") in (
                    "volunteering", "award", "publication", "patent", "sport",
                    "opensource", "exhibition", "grant", "press", "teaching", "license",
                )
            ]

            job.progress = 35
            job.add_log(
                f"✓ Found {len(skills)} skills, {len(selected_projects)} projects, "
                f"{len(selected_experiences)} experiences, {len(achievements)} achievements",
                "success",
            )
            time.sleep(0.8)

            # Stage 2: Clear existing career graph nodes
            job.status = "extracting"
            job.progress = 50
            job.add_log("🔄 Clearing existing Career Graph...", "info")
            session.query(CareerGraphNode).filter(CareerGraphNode.user_id == user_id).delete()
            session.commit()
            time.sleep(0.5)

            # Stage 3: Build nodes + edges
            job.status = "matching"
            job.progress = 70
            job.add_log("▸ Creating Career Graph nodes...", "info")

            nodes = []
            edges = []

            # Skill nodes — dedupe by name, aggregate multi-source confidence
            skill_agg: dict[str, dict] = {}
            for skill in skills:
                name = skill.skill_name
                if name not in skill_agg:
                    skill_agg[name] = {"confidences": [], "sources": set(), "skill_id": skill.skill_id}
                skill_agg[name]["confidences"].append(skill.confidence_score)
                skill_agg[name]["sources"].add(skill.source)
                if skill.skill_id and not skill_agg[name]["skill_id"]:
                    skill_agg[name]["skill_id"] = skill.skill_id

            for name, agg in skill_agg.items():
                node_id = f"skill_{name}"
                avg_conf = round(sum(agg["confidences"]) / len(agg["confidences"]), 3)
                nodes.append(GraphNode(
                    id=node_id, type="skill", label=name,
                    confidence=avg_conf,
                    metadata={"evidence_count": len(agg["confidences"]), "sources": sorted(agg["sources"])}
                ))
                session.add(CareerGraphNode(
                    user_id=user_id, node_type="skill", label=name,
                    canonical_id=str(agg["skill_id"]) if agg["skill_id"] else None,
                    confidence=avg_conf,
                    node_metadata={"sources": sorted(agg["sources"]), "evidence_count": len(agg["confidences"])}
                ))

            skills_by_name = {name.lower(): name for name in skill_agg}

            # Project nodes + edges
            for proj in selected_projects:
                proj_id = f"project_{proj.id}"
                techs = (proj.evidence_data or {}).get("technologies", [])
                nodes.append(GraphNode(
                    id=proj_id, type="project", label=proj.skill_name,
                    confidence=proj.confidence_score, metadata={"technologies": techs}
                ))
                session.add(CareerGraphNode(
                    user_id=user_id, node_type="project", label=proj.skill_name,
                    confidence=proj.confidence_score,
                    node_metadata={
                        "source_type": proj.source,
                        "technologies": techs,
                        "description": (proj.evidence_data or {}).get("description", "")
                    }
                ))
                for tech in techs:
                    canonical = skills_by_name.get(tech.lower())
                    if canonical:
                        edges.append(GraphEdge(source=proj_id, target=f"skill_{canonical}", weight=0.8))

            # Experience (company) nodes + edges
            for exp in selected_experiences:
                exp_id = f"experience_{exp.id}"
                techs = (exp.evidence_data or {}).get("technologies", [])
                nodes.append(GraphNode(
                    id=exp_id, type="company", label=exp.skill_name,
                    confidence=exp.confidence_score,
                    metadata={"company": (exp.evidence_data or {}).get("company", "")}
                ))
                session.add(CareerGraphNode(
                    user_id=user_id, node_type="experience", label=exp.skill_name,
                    confidence=exp.confidence_score,
                    node_metadata={
                        "source_type": exp.source,
                        "company": (exp.evidence_data or {}).get("company", ""),
                        "role": (exp.evidence_data or {}).get("role", ""),
                        "duration": (exp.evidence_data or {}).get("duration", ""),
                        "technologies": techs
                    }
                ))
                for tech in techs:
                    canonical = skills_by_name.get(tech.lower())
                    if canonical:
                        edges.append(GraphEdge(source=exp_id, target=f"skill_{canonical}", weight=0.8))

            # Achievement nodes — gold, externally-validated proof
            for ach in achievements:
                ach_id = f"achievement_{ach.id}"
                kind = (ach.evidence_data or {}).get("type", "award")
                nodes.append(GraphNode(
                    id=ach_id, type="achievement", label=ach.skill_name,
                    confidence=ach.confidence_score,
                    metadata={"kind": kind, "year": (ach.evidence_data or {}).get("year")},
                ))
                session.add(CareerGraphNode(
                    user_id=user_id, node_type="achievement", label=ach.skill_name,
                    confidence=ach.confidence_score,
                    node_metadata={
                        "kind": kind,
                        "detail": (ach.evidence_data or {}).get("detail", ""),
                        "year": (ach.evidence_data or {}).get("year"),
                    },
                ))

            job.progress = 85
            job.add_log(f"✓ Positioned {len(nodes)} nodes and {len(edges)} connections", "success")
            time.sleep(0.8)

            job.progress = 95
            job.add_log("📊 Finalizing Career Graph...", "success")

            # Stats — sadece GERÇEK hesaplananlar. matched_jobs/strong_matches
            # job matching geldiğinde (C aşaması), experience_years/total_commits
            # gerçek kaynaklardan beslenince eklenecek.
            graph = CareerGraph(
                nodes=nodes,
                edges=edges,
                stats={
                    "skills_count": len(skill_agg),
                    "projects_count": len(selected_projects),
                    "companies_count": len(selected_experiences),
                    "achievements_count": len(achievements),
                    "edges_count": len(edges),
                    "confidence_score": round(sum(n.confidence for n in nodes) / len(nodes), 3) if nodes else 0.0,
                }
            )

            session.commit()

            job.result = graph.dict()
            job.progress = 100
            job.status = "completed"
            job.add_log("✓ Career Graph ready", "success")

            repo = UserRepository(session)
            repo.set_onboarding_state(user_id, OnboardingState.READY)
            repo.patch_profile_data(user_id, {"career_graph": graph.dict()})
            session.commit()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.add_log(f"✗ Graph building failed: {e}", "error")


@router.get("/build-graph/{job_id}/status")
async def get_graph_building_status(
    job_id: str,
    user_id: str = Depends(get_user_id),
):
    """Poll graph building job status."""
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = extraction_jobs[job_id]
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return job.to_dict()


@router.get("/career-graph")
def get_career_graph(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Get user's Career Graph nodes and edges."""
    repo = UserRepository(session)
    user = _require_user(repo, user_id)
    return user.profile_data.get("career_graph") or {"nodes": [], "edges": [], "stats": {}}


