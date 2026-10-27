"""Evidence — proof behind a user's skills.

Single source of truth: the `evidence_items` table (core.db.models.EvidenceItem).
Every source writes there; every consumer (API, scoring, resume generation,
briefing) reads from there.

    skills.py       match free-text skill names to the canonical `skills` taxonomy
    aggregation.py  combine items across sources into one confidence per skill
    github.py       GitHub repos (OAuth token) → project + language evidence
    portfolio.py    portfolio website → project + technology evidence
    resume.py       uploaded CV (PDF) → skills, experience, projects, achievements
    resume_llm.py   the LLM extraction step used by resume.py

The legacy `evidence` table (core.db.models.Evidence) is no longer read or
written; its rows are kept in the database untouched.
"""
