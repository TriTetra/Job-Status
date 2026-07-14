"""Learning Memory — optimal study patterns and preferences (in-memory)."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseMemory, MemoryFact


class LearningMemory(BaseMemory):
    """
    Stores learning patterns derived from user behaviour.

    In-memory only; future: persist and analyse across sessions.
    """

    def __init__(self, user_id: str = "default"):
        super().__init__(user_id)
        self._facts: List[MemoryFact] = []

    def add_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        expires_after_days: Optional[int] = None,
    ) -> MemoryFact:
        expires_at = None
        if expires_after_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_after_days)

        fact = MemoryFact(
            fact_type=fact_type,
            content=content,
            confidence=confidence,
            metadata=metadata or {},
            expires_at=expires_at,
            source=source,
        )
        self._facts.append(fact)
        return fact

    def get_facts(
        self,
        fact_type: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[MemoryFact]:
        facts = self._facts
        if not include_expired:
            facts = [f for f in facts if not f.is_expired()]
        if fact_type:
            facts = [f for f in facts if f.fact_type == fact_type]
        return sorted(facts, key=lambda f: f.created_at, reverse=True)[:limit]

    def clear(self):
        self._facts.clear()

    def get_optimal_study_plan(self) -> Dict[str, Any]:
        """Derive study plan from stored facts, with sensible defaults."""
        hours_facts = self.get_facts(fact_type="optimal_hours")
        hours = 10
        if hours_facts:
            hours = hours_facts[0].metadata.get("hours", 10)

        return {
            "hours_per_week": hours,
            "preferred_format": "project",
            "preferred_time": "evening",
            "recommendation": f"Focus on project-based learning with {hours} hours/week",
        }
