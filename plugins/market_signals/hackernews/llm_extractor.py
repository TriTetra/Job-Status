"""LLM job extraction — hybrid Layer-2, profession-agnostic."""

import json
import logging
import os
import re
from typing import List

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-4o-mini")

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
    Raises on HTTP errors or JSON parse failures.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set — set it to enable LLM extraction")

    n = len(comment_texts)
    blocks = "\n\n".join(
        f"---COMMENT {i + 1}---\n{t[:1500]}" for i, t in enumerate(comment_texts)
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": EXTRACT_PROMPT.format(n=n, blocks=blocks),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 2500,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://applypilot.local",
        "X-Title": "ApplyPilot",
    }

    resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    raw = json.loads(content)
    if not isinstance(raw, list):
        raw = [raw]

    # Pad or trim to match requested n
    results: List[LLMJob] = []
    for i in range(n):
        item = raw[i] if i < len(raw) else {}
        results.append(LLMJob.model_validate(item) if isinstance(item, dict) else LLMJob())

    return results
