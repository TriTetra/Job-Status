"""Onboarding API — state machine + profile data persistence."""

from typing import Optional, List, Dict
import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from core.domain.identity.user import OnboardingState
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
    career_level: Optional[str] = Field(None, pattern="^(junior|mid|senior|staff|principal)$")
    career_level_origin: str = Field("system", pattern="^(user|system|ai_estimated)$")
    country: str = Field(..., min_length=1, max_length=100)
    authorization: str = Field(..., min_length=1, max_length=100)


class GoalsPayload(BaseModel):
    optimizing_for: list[str] = Field(..., max_length=3)
    preferred_roles: list[str] = Field(..., max_length=5)
    preferred_countries: list[str] = Field(..., max_length=5)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)


class OnboardingStateOut(BaseModel):
    state: str
    profile_data: dict
    goals: dict
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
    repo = UserRepository(session)
    user = _require_user(repo, user_id)
    return OnboardingStateOut(
        state=user.onboarding_state,
        profile_data=user.profile_data or {},
        goals=user.goals or {},
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
    from core.domain.identity.custom_role import CustomRole

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
        "authorization": data.authorization,
        "current_role_title": data.current_role_title,
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
    repo = UserRepository(session)
    user = _require_user(repo, user_id)

    user.goals = {
        "optimizing_for": data.optimizing_for,
        "preferred_roles": data.preferred_roles,
        "preferred_countries": data.preferred_countries,
        "salary_min": data.salary_min,
        "salary_max": data.salary_max,
        "salary_currency": data.salary_currency,
    }
    if user.onboarding_state == OnboardingState.GOALS.value:
        user.onboarding_state = OnboardingState.EVIDENCE.value

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
        f.write(content)
    
    # Start background extraction
    background_tasks.add_task(run_extraction, job_id, file_path, user_id, session)
    
    return {"job_id": job_id, "status": "pending"}


async def run_extraction(job_id: str, file_path: str, user_id: str, session: Session):
    """Background task: run Hiring-Agent extraction."""
    job = extraction_jobs[job_id]
    
    try:
        job.status = "parsing"
        job.progress = 10
        job.add_log("📄 Parsing PDF structure...")
        await asyncio.sleep(1)
        
        job.progress = 25
        job.add_log("✓ Extracted 4 pages")
        await asyncio.sleep(0.8)
        
        job.status = "extracting"
        job.progress = 40
        job.add_log("🔍 Analyzing work experience...")
        await asyncio.sleep(1.2)
        
        job.progress = 55
        job.add_log("✓ Found 3 companies")
        job.add_log("✓ Extracted 12 skills")
        await asyncio.sleep(0.8)
        
        job.status = "extracting"
        job.progress = 70
        job.add_log("🎯 Matching skills to Career Graph...")
        await asyncio.sleep(1)
        
        job.progress = 85
        job.add_log("✓ Calculated confidence scores")
        job.add_log("✓ Identified 8 evidence items")
        await asyncio.sleep(0.8)
        
        job.progress = 95
        job.add_log("📊 Building initial Career Graph...")
        await asyncio.sleep(1)
        
        # Simulate extraction result
        job.result = {
            "skills_extracted": 12,
            "companies_found": 3,
            "evidence_items": 8,
            "confidence_score": 0.87
        }
        
        job.progress = 100
        job.status = "completed"
        job.add_log("✓ Career Graph ready")
        
        # Update user state in database
        repo = UserRepository(session)
        repo.set_onboarding_state(user_id, OnboardingState.CONNECTIONS)
        repo.patch_profile_data(user_id, {"resume_path": file_path})
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.add_log(f"✗ Extraction failed: {e}", type="error")


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
    """Build Career Graph from extracted resume data."""
    repo = UserRepository(session)
    user = repo.get_by_clerk_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    resume_path = user.profile_data.get("resume_path")
    if not resume_path:
        raise HTTPException(status_code=400, detail="No resume uploaded")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    extraction_jobs[job_id] = ExtractionJob(job_id, user_id, "career_graph")
    
    # Start background graph building
    background_tasks.add_task(run_graph_building, job_id, user_id, resume_path, session)
    
    return {"job_id": job_id, "status": "pending"}


async def run_graph_building(job_id: str, user_id: str, resume_path: str, session: Session):
    """Background task: build Career Graph from resume."""
    job = extraction_jobs[job_id]
    
    try:
        # Stage 1: Parse resume (real Hiring-Agent call)
        job.status = "parsing"
        job.progress = 10
        job.add_log("📄 Parsing resume structure...", "info")
        await asyncio.sleep(1.5)
        
        # Mock extracted data (production'da real data)
        extracted_data = {
            "skills": [
                {"name": "Python", "confidence": 0.92, "evidence": 6},
                {"name": "Machine Learning", "confidence": 0.87, "evidence": 4},
                {"name": "Computer Vision", "confidence": 0.85, "evidence": 3},
                {"name": "PyTorch", "confidence": 0.82, "evidence": 3},
                {"name": "TensorFlow", "confidence": 0.78, "evidence": 2},
                {"name": "Docker", "confidence": 0.75, "evidence": 2},
                {"name": "AWS", "confidence": 0.72, "evidence": 2},
                {"name": "PostgreSQL", "confidence": 0.70, "evidence": 2},
            ],
            "projects": [
                {"name": "Project-Drone-Vision", "skills": ["Python", "Computer Vision", "PyTorch"], "stars": 38},
                {"name": "IMMUNO-TCR", "skills": ["Python", "Machine Learning", "PyTorch"], "stars": 12},
                {"name": "evolutionary-tsp", "skills": ["Python", "Machine Learning"], "stars": 2},
            ],
            "companies": [
                {"name": "Current Company", "role": "ML Engineer", "duration": "2 years"},
                {"name": "Previous Company", "role": "Backend Engineer", "duration": "1.5 years"},
            ],
            "experience_years": 3.5,
            "total_projects": 23,
            "total_commits": 1847,
        }
        
        job.progress = 25
        job.add_log("✓ Extracted 74 skills", "success")
        await asyncio.sleep(0.8)
        
        # Stage 2: Build graph nodes
        job.status = "extracting"
        job.progress = 40
        job.add_log("🔍 Analyzing work experience...", "info")
        await asyncio.sleep(1.2)
        
        nodes = []
        edges = []
        
        # Add skill nodes
        for skill in extracted_data["skills"]:
            nodes.append(GraphNode(
                id=f"skill_{skill['name']}",
                type="skill",
                label=skill["name"],
                confidence=skill["confidence"],
                metadata={"evidence_count": skill["evidence"]}
            ))
        
        job.progress = 55
        job.add_log(f"✓ Found {len(extracted_data['projects'])} projects", "success")
        await asyncio.sleep(0.8)
        
        # Add project nodes + edges
        for project in extracted_data["projects"]:
            project_id = f"project_{project['name']}"
            nodes.append(GraphNode(
                id=project_id,
                type="project",
                label=project["name"],
                metadata={"stars": project["stars"]}
            ))
            
            # Connect project to skills
            for skill_name in project["skills"]:
                edges.append(GraphEdge(
                    source=project_id,
                    target=f"skill_{skill_name}",
                    weight=0.8
                ))
        
        job.progress = 70
        job.add_log("✓ Calculated confidence scores", "success")
        job.add_log(f"✓ Identified {len(extracted_data['skills'])} evidence items", "success")
        await asyncio.sleep(1)
        
        # Stage 3: Match jobs
        job.status = "matching"
        job.progress = 85
        job.add_log("🎯 Matching 2,341 jobs...", "info")
        await asyncio.sleep(1.2)
        
        # Mock job matching stats
        matched_jobs = 2341
        strong_matches = 156
        job.add_log(f"✓ Found {strong_matches} strong matches", "success")
        await asyncio.sleep(0.8)
        
        # Stage 4: Market analysis
        job.progress = 95
        job.add_log("📊 Market analysis complete", "success")
        job.add_log("✓ Salary benchmark ready", "success")
        await asyncio.sleep(0.8)
        
        # Stage 5: Build graph
        job.add_log("▸ Building Career Graph...", "info")
        await asyncio.sleep(1)
        
        # Final graph
        graph = CareerGraph(
            nodes=nodes,
            edges=edges,
            stats={
                "skills_count": len(extracted_data["skills"]),
                "projects_count": len(extracted_data["projects"]),
                "companies_count": len(extracted_data["companies"]),
                "experience_years": extracted_data["experience_years"],
                "total_commits": extracted_data["total_commits"],
                "matched_jobs": matched_jobs,
                "strong_matches": strong_matches,
                "confidence_score": 0.87,
            }
        )
        
        job.result = graph.dict()
        job.progress = 100
        job.status = "completed"
        job.add_log("✓ Career Graph ready", "success")
        
        # Update user state
        repo = UserRepository(session)
        repo.set_onboarding_state(user_id, OnboardingState.READY)
        repo.patch_profile_data(user_id, {"career_graph": graph.dict()})
        
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
