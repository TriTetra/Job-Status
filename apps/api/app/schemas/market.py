"""Market intelligence schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MarketSignalResponse(BaseModel):
    id: int
    signal_type: str
    source: str
    title: str
    impact: str
    occurred_at: datetime
    companies_affected: List[str] = []
    skills_affected: List[str] = []
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class SkillTrendResponse(BaseModel):
    skill: str
    current_count: int
    previous_count: int
    change_percent: float
    direction: str


class MarketSummaryResponse(BaseModel):
    period_days: int
    signal_counts: dict
    top_companies: List[dict]
    top_skills: List[dict]
