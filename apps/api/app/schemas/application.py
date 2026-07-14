"""Application schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    url: str
    title: str
    company: Optional[str] = None
    status: str = "to_apply"


class ApplicationUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    url: str
    title: str
    company: Optional[str] = None
    status: str
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PipelineSummary(BaseModel):
    counts: dict
