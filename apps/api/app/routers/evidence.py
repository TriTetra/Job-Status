"""Evidence router — skill confidence from GitHub projects."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from core.db.repositories import EvidenceRepository

router = APIRouter()


class EvidenceResponse(BaseModel):
    skill_name: str
    project_name: str
    confidence: float
    author_commits: int = 0
    stars: int = 0
    github_url: str = ""
    evidence_type: str = ""

    class Config:
        from_attributes = True


class SkillSummary(BaseModel):
    skill: str
    evidence_count: int
    avg_confidence: float
    total_commits: int
    total_stars: int


@router.get("/", response_model=List[EvidenceResponse])
def list_evidence(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """All evidence rows for the user."""
    repo = EvidenceRepository(session)
    rows = repo.get_all_evidence_for_user(user_id=user_id)
    return [EvidenceResponse.model_validate(e) for e in rows]


@router.get("/summary", response_model=List[SkillSummary])
def skill_summary(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Per-skill confidence summary."""
    repo = EvidenceRepository(session)
    data: Dict[str, Any] = repo.skill_summary(user_id=user_id)
    return [
        SkillSummary(
            skill=skill,
            evidence_count=v["evidence_count"],
            avg_confidence=v["avg_confidence"],
            total_commits=v["total_commits"],
            total_stars=v["total_stars"],
        )
        for skill, v in data.items()
    ]


@router.get("/{skill}", response_model=List[EvidenceResponse])
def evidence_for_skill(
    skill: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Evidence rows for a specific skill."""
    repo = EvidenceRepository(session)
    rows = repo.get_for_skill(skill_name=skill, user_id=user_id)
    return [EvidenceResponse.model_validate(e) for e in rows]
