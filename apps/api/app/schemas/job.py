"""Job schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class JobWithScore(BaseModel):
    url: str
    career_score: Optional[float] = None
    fit_score: Optional[float] = None
    acceptance_probability: Optional[float] = None
    career_value: Optional[float] = None
    market_demand: Optional[float] = None
    expected_value: Optional[float] = None
    recommendation: Optional[str] = None
    skill_gaps: List[str] = []
    explanation: Dict[str, Any] = {}
    scanned_at: Optional[str] = None
    user_decision: Dict[str, Any] = {"status": "unreviewed", "decided_at": None}

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobWithScore]
