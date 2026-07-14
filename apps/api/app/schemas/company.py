"""Company schemas."""

from typing import List, Optional

from pydantic import BaseModel


class CompanyResponse(BaseModel):
    name: str
    tier: str = "unknown"
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    tech_stack: List[str] = []
    hiring_trend: str = "stable"
    open_positions_count: int = 0
    culture_signals: List[str] = []

    class Config:
        from_attributes = True


class CompanyMemoryResponse(BaseModel):
    company: str
    total_interactions: int
    application_count: int = 0
    rejection_count: int = 0
    interview_count: int = 0
    offer_count: int = 0
    interview_topics_asked: List[str] = []
