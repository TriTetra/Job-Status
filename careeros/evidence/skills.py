"""Match free-text skill names to canonical Skill records in DB."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from careeros.evidence.models.skill import Skill
from careeros.knowledge.skill_names import compact

logger = logging.getLogger(__name__)


def find_canonical(skill_name: str, all_skills: list[Skill]) -> Optional[Skill]:
    """The canonical Skill for a name, or None.

    Exact name, then alias, then the same spelling-insensitively ("Hugging Face" =
    "HuggingFace", "Node.js" = "nodejs"). No fuzzy matching: "OpenAlex API" is not
    "OpenAI API", and a wrong merge is worse than an unmatched name (unmatched names
    still score by name).
    """
    target = skill_name.lower().strip()

    # 1. Exact name match
    for s in all_skills:
        if s.name.lower() == target:
            return s

    # 2. Alias match
    for s in all_skills:
        for alias in (s.aliases or []):
            if alias.lower() == target:
                return s

    # 3. Spelling-insensitive name / alias match
    key = compact(target)
    for s in all_skills:
        if compact(s.name) == key or any(compact(a) == key for a in (s.aliases or [])):
            return s
    return None


def load_all_skills(db: Session) -> list[Skill]:
    return db.query(Skill).filter(Skill.is_deprecated == False).all()
