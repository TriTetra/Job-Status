"""LLM-based structured resume extraction via OpenRouter."""

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-4o-mini")

SYSTEM_PROMPT = "You are a precise resume parser. Return only valid JSON, no markdown."

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
  "certifications": ["..."]
}}

Confidence rules for skills:
- 0.90–1.0  → in dedicated Skills section OR used across 3+ projects/jobs
- 0.70–0.89 → named in project/job description
- 0.50–0.69 → mentioned once in passing

Extract every technology, framework, language, and tool mentioned.
Return empty arrays [] for sections not present.

Resume:
{text}"""


def extract_resume(text: str) -> dict[str, Any]:
    """Call OpenRouter to extract structured data from resume text."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    prompt = EXTRACT_PROMPT.format(text=text[:12000])  # stay within context window

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 3000,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://applypilot.local",
        "X-Title":       "ApplyPilot",
    }

    resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code block if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    data = json.loads(content)
    logger.info(
        "Extracted %d skills, %d experiences, %d projects",
        len(data.get("skills", [])),
        len(data.get("experience", [])),
        len(data.get("projects", [])),
    )
    return data
