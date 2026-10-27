"""Match free-text skill names to canonical Skill records in DB."""

import logging
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from core.db.models.skill import Skill

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.80


def find_canonical(skill_name: str, all_skills: list[Skill]) -> Optional[Skill]:
    """Return the best-matching canonical Skill, or None."""
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

    # 3. Fuzzy match
    best: Optional[Skill] = None
    best_score = 0.0
    for s in all_skills:
        score = SequenceMatcher(None, s.name.lower(), target).ratio()
        if score > best_score and score >= SIMILARITY_THRESHOLD:
            best_score = score
            best = s

    if best:
        logger.debug("Fuzzy matched '%s' → '%s' (%.2f)", skill_name, best.name, best_score)
    return best


def load_all_skills(db: Session) -> list[Skill]:
    return db.query(Skill).filter(Skill.is_deprecated == False).all()
