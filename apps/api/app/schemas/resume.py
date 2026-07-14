"""Resume schemas."""

from pydantic import BaseModel


class ResumeGenerateRequest(BaseModel):
    target_company: str
    target_title: str
    template_name: str = "ml_research"
    job_description: str = ""
    user_id: str = "default"


class ResumeGenerateResponse(BaseModel):
    output_path: str
    target_company: str
    target_title: str
    template_used: str
    size_chars: int
    lines: int
