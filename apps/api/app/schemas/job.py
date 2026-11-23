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
    # Decision Contract v1 (tier, criteria, next action, reasoning) — the web reads it here
    decision: Optional[Dict[str, Any]] = None
    scanned_at: Optional[str] = None
    user_decision: Dict[str, Any] = {"status": "unreviewed", "decided_at": None}

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobWithScore]


class JobSearchItem(JobWithScore):
    # False: scored just now for this search (not one of your Opportunities, not saved)
    in_opportunities: bool = False


class JobSearchResponse(BaseModel):
    total: int
    capped: bool = False  # more postings matched than one search reads: narrow it
    country: Optional[str] = None  # the country searched, also when it was typed in the box ("İstanbul")
    jobs: List[JobSearchItem]
