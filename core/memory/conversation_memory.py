"""Conversation Memory — LLM context persistence (in-memory)."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseMemory, MemoryFact


class ConversationMemory(BaseMemory):
    """
    Keeps recent LLM conversation context.

    In-memory only; each process starts fresh.
    Future: persist to DB for cross-session continuity.
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

    def get_context_for_prompt(self, max_facts: int = 10) -> str:
        """Return formatted context string for injection into LLM prompts."""
        facts = self.get_facts(limit=max_facts)
        if not facts:
            return ""
        lines = ["Previous conversation context:"]
        for fact in facts:
            lines.append(f"- {fact.content}")
        return "\n".join(lines)
