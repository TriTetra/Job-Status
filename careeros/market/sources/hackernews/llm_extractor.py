"""LLM job extraction — hybrid Layer-2, profession-agnostic."""

import logging
from typing import List

from pydantic import BaseModel, Field

from careeros.shared.llm import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a precise job-posting parser. Return only valid JSON, no markdown."

EXTRACT_PROMPT = """\
Below are {n} job posting comments separated by markers.
For EACH comment extract:
- company (hiring organization name, empty string if unclear)
- role (job title)
- skills (tools, technologies, methodologies, certifications, competencies —
  ANY profession: engineering, medical, legal, design, marketing, education, trades…)
- remote (true/false)
- sponsors_visa (true/false)

Return a JSON array with exactly {n} objects, in the same order as the comments:
[{{"company": "...", "role": "...", "skills": ["..."], "remote": false, "sponsors_visa": false}}]

{blocks}"""


class LLMJob(BaseModel):
    company: str = ""
    role: str = ""
    skills: List[str] = Field(default_factory=list)
    remote: bool = False
    sponsors_visa: bool = False


def extract_batch(comment_texts: List[str]) -> List[LLMJob]:
    """
    One LLM call for a batch of job-posting comments.
    Returns one LLMJob per comment (same order, empty objects for unparseable).
    Raises shared.llm.LLMError (incl. LLMNotConfiguredError) on failure.
    """
    n = len(comment_texts)
    blocks = "\n\n".join(
        f"---COMMENT {i + 1}---\n{t[:1500]}" for i, t in enumerate(comment_texts)
    )

    raw = get_llm_client().complete_json(
        EXTRACT_PROMPT.format(n=n, blocks=blocks),
        system=SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=2500,
        timeout=120,
    )
    if not isinstance(raw, list):
        raw = [raw]

    # Pad or trim to match requested n
    results: List[LLMJob] = []
    for i in range(n):
        item = raw[i] if i < len(raw) else {}
        results.append(LLMJob.model_validate(item) if isinstance(item, dict) else LLMJob())

    return results
