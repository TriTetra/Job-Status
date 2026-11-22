"""LLM-based structured resume extraction (through the LLM gateway)."""

import logging
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from careeros.knowledge.skill_names import known_names
from careeros.shared.llm import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a precise resume parser. Return only valid JSON, no markdown."

# Enough for a long CV; longer text is cut (and logged) rather than sent whole
MAX_RESUME_CHARS = 20000
# Thinking counts towards this ceiling, so it is generous; the prompt keeps output short
MAX_OUTPUT_TOKENS = 12000

ACHIEVEMENT_TYPES = {
    "volunteering", "award", "publication", "patent", "sport", "opensource",
    "exhibition", "grant", "press", "teaching", "license",
}
# Still under review / in progress: claimed, not yet externally validated
PENDING_STATUSES = {"submitted", "under_review", "in_progress"}


class _Loose(BaseModel):
    model_config = ConfigDict(extra="ignore")


def _text(v: Any) -> str:
    return "" if v is None else str(v).strip()


class ExtractedSkill(_Loose):
    name: str
    confidence: float = 0.7
    evidence: str = ""

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, v: Any) -> float:
        try:
            return min(1.0, max(0.0, float(v)))
        except (TypeError, ValueError):
            return 0.7

    @field_validator("name", "evidence", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _text(v)


class ExtractedExperience(_Loose):
    company: str = ""
    role: str = ""
    duration: str = ""
    technologies: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)  # measurable results, as written

    @field_validator("company", "role", "duration", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _text(v)


class ExtractedProject(_Loose):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""

    @field_validator("name", "description", "url", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _text(v)


class ExtractedEducation(_Loose):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""

    @field_validator("institution", "degree", "field", "year", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _text(v)


class ExtractedAchievement(_Loose):
    """High-value, externally-validated evidence that is NOT a job or project.

    These are the signals most systems silently drop — we treat them as
    first-class evidence because a medal or a Nature paper outweighs a claim.
    `status` separates a granted award or published paper from one still pending.
    """
    type: str = "award"
    title: str
    detail: str = ""
    year: Optional[str] = None
    status: str = "completed"  # completed | submitted | under_review | in_progress

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # Some models answer "category" / "description" despite the prompt
        if "category" in data and "type" not in data:
            data["type"] = data.pop("category")
        if "description" in data and "detail" not in data:
            data["detail"] = data.pop("description")
        if str(data.get("type", "")).lower() not in ACHIEVEMENT_TYPES:
            data["type"] = "award"
        data["type"] = str(data["type"]).lower()
        status = str(data.get("status") or "completed").lower().replace(" ", "_")
        data["status"] = status if status in PENDING_STATUSES | {"completed"} else "completed"
        if data.get("year") is not None:
            data["year"] = _text(data["year"]) or None
        data["detail"] = _text(data.get("detail"))
        return data

    @property
    def pending(self) -> bool:
        return self.status in PENDING_STATUSES


class StructuredResume(_Loose):
    skills: list[ExtractedSkill] = Field(default_factory=list)
    experience: list[ExtractedExperience] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    education: list[ExtractedEducation] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[ExtractedAchievement] = Field(default_factory=list)

    @field_validator("skills", "experience", "projects", "education", "achievements", mode="before")
    @classmethod
    def _drop_unnamed(cls, v: Any) -> Any:
        # A stray string or null in a list should not sink the whole CV
        return [x for x in (v or []) if isinstance(x, dict)]

    @field_validator("certifications", mode="before")
    @classmethod
    def _cert_strings(cls, v: Any) -> list[str]:
        out = []
        for x in v or []:
            name = x.get("name") or x.get("title") if isinstance(x, dict) else x
            if _text(name):
                out.append(_text(name))
        return out


EXTRACT_PROMPT = """\
Parse the resume text below and return a JSON object with this exact shape:

{{
  "skills": [
    {{"name": "...", "confidence": 0.9, "evidence": "where it appears, at most 8 words"}}
  ],
  "experience": [
    {{"company": "...", "role": "...", "duration": "...", "technologies": ["..."],
      "highlights": ["measurable result, as written"]}}
  ],
  "projects": [
    {{"name": "...", "description": "one sentence", "technologies": ["..."], "url": ""}}
  ],
  "education": [
    {{"institution": "...", "degree": "...", "field": "...", "year": "..."}}
  ],
  "certifications": ["..."],
  "achievements": [
    {{
      "type": "volunteering | award | publication | patent | sport | opensource | exhibition | grant | press | teaching | license",
      "title": "string",
      "detail": "string (issuer, journal, team, repo — whatever proves it)",
      "year": "string (optional)",
      "status": "completed | submitted | under_review | in_progress"
    }}
  ]
}}

Rules:
1. Skill names: one technology, framework, language, tool or method per entry, written
   plainly WITHOUT versions or qualifiers — "React" not "React 19", "PostgreSQL" not
   "PostgreSQL 17", "Redis" and "Asynq" as two entries, never "Redis (Asynq)" or "A / B".
   When one of these catalog names fits, use it exactly: {catalog}
2. Confidence for skills:
   - 0.90–1.0  → in a dedicated Skills section AND used in a job or project, or used across 3+ jobs/projects
   - 0.75–0.89 → used in a job or project description, or only listed in a Skills section
   - 0.50–0.74 → mentioned once in passing, or only in coursework
   Spread the scores honestly; do not give everything 0.9.
3. Extract every technology, framework, language, and tool mentioned. Keep "evidence" short.
4. Experience "highlights": up to 3 per job, only results with a number or a concrete
   outcome (e.g. "30% faster first paint", "92% mAP on 30,000 images"), copied faithfully.
5. Return empty arrays [] for sections not present. Use only the field names shown above.
6. Achievements: volunteering, awards, honors, publications, patents, sports results
   (medals, national/international team), open-source maintainer / committer roles,
   exhibitions, grants and fellowships, press, teaching, and professional licenses.
   These are HIGH-VALUE evidence — never fold them into experience, never skip them.
   Put the proving detail (journal, awarding body, team, repository) in "detail".
   A gallery / biennale show → exhibition; a fellowship or research funding → grant;
   an interview or feature → press; a course taught or thesis supervised → teaching;
   a license to practice (bar, medical board, CPA, pilot) → license, never a certification.
7. Achievement "status": "completed" when granted / published / won; "submitted" or
   "under_review" when the resume says submitted, under review, pending; "in_progress"
   when ongoing. Never mark a submission as completed.

Resume:
{text}"""


def extract_resume(text: str, user_id: Optional[str] = None) -> StructuredResume:
    """Structured data from resume text, validated (one corrective retry on bad JSON)."""
    if len(text) > MAX_RESUME_CHARS:
        logger.warning("Resume text cut from %d to %d chars", len(text), MAX_RESUME_CHARS)
    prompt = EXTRACT_PROMPT.format(catalog=", ".join(known_names()), text=text[:MAX_RESUME_CHARS])

    structured = get_llm_client().complete_model(
        prompt, StructuredResume, system=SYSTEM_PROMPT, task="cv_extract", user_id=user_id,
        temperature=0.1, max_tokens=MAX_OUTPUT_TOKENS, timeout=180,
    )
    logger.info(
        "Extracted %d skills, %d experiences, %d projects, %d achievements",
        len(structured.skills), len(structured.experience),
        len(structured.projects), len(structured.achievements),
    )
    return structured
