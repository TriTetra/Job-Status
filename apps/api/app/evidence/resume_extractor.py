"""LLM-based structured resume extraction via OpenRouter."""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from shared.llm import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a precise resume parser. Return only valid JSON, no markdown."


class ExtractedAchievement(BaseModel):
    """High-value, externally-validated evidence that is NOT a job or project.

    type ∈ volunteering | award | publication | patent | sport | opensource | exhibition | grant | press | teaching | license
    These are the signals most systems silently drop — we treat them as
    first-class evidence because a medal or a Nature paper outweighs a claim.
    """
    type: str = Field(
        default="award",
        pattern="^(volunteering|award|publication|patent|sport|opensource|exhibition|grant|press|teaching|license)$",
    )
    title: str
    detail: str = ""
    year: Optional[str] = None


class StructuredResume(BaseModel):
    skills: list[dict] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[ExtractedAchievement] = Field(default_factory=list)


EXTRACT_PROMPT = """\
Parse the resume text below and return a JSON object with this exact shape:

{{
  "skills": [
    {{"name": "...", "confidence": 0.9, "evidence": "where mentioned"}}
  ],
  "experience": [
    {{"company": "...", "role": "...", "duration": "...", "technologies": ["..."]}}
  ],
  "projects": [
    {{"name": "...", "description": "...", "technologies": ["..."]}}
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
      "year": "string (optional)"
    }}
  ]
}}

Rules:
1. Confidence for skills:
   - 0.90–1.0  → in dedicated Skills section OR used across 3+ projects/jobs
   - 0.70–0.89 → named in project/job description
   - 0.50–0.69 → mentioned once in passing
2. Extract every technology, framework, language, and tool mentioned.
3. Return empty arrays [] for sections not present.
4. Use only the exact field names shown above.
5. For achievements.type use exactly one of:
   volunteering | award | publication | patent | sport | opensource | exhibition | grant | press | teaching | license
6. Extract volunteering, awards, honors, publications, patents, sports
   achievements (medals, national/international team), and open-source
   maintainer / committer roles as "achievements". These are HIGH-VALUE
   evidence — never fold them into experience, never skip them.
7. For each achievement, put the proving detail (journal name, awarding body,
   team, repository URL/name) in "detail". Confidence is high because they
   are externally validated.
8. The achievement "type" must be one of: volunteering, award, publication,
   patent, sport, opensource, exhibition, grant, press, teaching, license.
   Map a gallery / biennale / salon show → exhibition; a fellowship or
   research funding → grant; an interview or feature article → press; a
   course taught or thesis supervised → teaching; a professional license to
   practice (bar admission, medical board, CPA, pilot license) → license.
   A license is authority to practice, not a certificate — never fold it
   into certifications.

Resume:
{text}"""


def extract_resume(text: str) -> StructuredResume:
    """Call OpenRouter to extract structured data from resume text.

    Returns a StructuredResume with validated achievements.
    Falls back gracefully if the LLM omits the achievements key.
    """
    prompt = EXTRACT_PROMPT.format(text=text[:12000])  # stay within context window

    raw: dict[str, Any] = get_llm_client().complete_json(
        prompt, system=SYSTEM_PROMPT, temperature=0.1, max_tokens=3500, timeout=120
    )

    # Normalise achievement entries: accept both "category" and "type" keys
    # (some models return "category" despite the prompt saying "type")
    for ach in raw.get("achievements", []):
        if "category" in ach and "type" not in ach:
            ach["type"] = ach.pop("category")
        if "description" in ach and "detail" not in ach:
            ach["detail"] = ach.pop("description")
        # Clamp to allowed values
        ALLOWED = {
            "volunteering", "award", "publication", "patent", "sport",
            "opensource", "exhibition", "grant", "press", "teaching", "license"
        }
        if ach.get("type") not in ALLOWED:
            ach["type"] = "award"

    structured = StructuredResume.model_validate(raw)

    logger.info(
        "Extracted %d skills, %d experiences, %d projects, %d achievements",
        len(structured.skills),
        len(structured.experience),
        len(structured.projects),
        len(structured.achievements),
    )
    return structured
