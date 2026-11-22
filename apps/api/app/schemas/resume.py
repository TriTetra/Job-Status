"""Resume schemas."""

from pydantic import BaseModel, Field


class ResumeGenerateRequest(BaseModel):
    target_company: str = Field(..., min_length=1, max_length=200)
    target_title: str = Field(..., min_length=1, max_length=200)
    template_name: str = Field("ml_research", max_length=64)
    # Goes into LLM prompts: bounded so one request can't burn the budget
    job_description: str = Field("", max_length=20_000)


class ResumeGenerateResponse(BaseModel):
    output_path: str
    target_company: str
    target_title: str
    template_used: str
    size_chars: int
    lines: int
