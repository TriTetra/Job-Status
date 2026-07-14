"""Market Memory — skill trend cache backed by market_signals table."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from packages.db.connection import db
from packages.db.repositories import MarketSignalRepository

from .base import BaseMemory, MemoryFact


class MarketMemory(BaseMemory):
    """
    Provides memory-layer access to market signals.

    add_fact() writes a signal row; get_facts() reads recent signals.
    """

    def __init__(self, user_id: str = "default"):
        super().__init__(user_id)

    def add_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        expires_after_days: Optional[int] = None,
    ) -> MemoryFact:
        with db.session_scope() as session:
            repo = MarketSignalRepository(session)
            repo.add_signal(
                signal_type=fact_type,
                source=source,
                title=content,
                occurred_at=datetime.utcnow(),
                impact="medium",
                metadata_json=metadata or {},
            )

        return MemoryFact(
            fact_type=fact_type,
            content=content,
            confidence=confidence,
            metadata=metadata or {},
            source=source,
        )

    def get_facts(
        self,
        fact_type: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[MemoryFact]:
        with db.session_scope() as session:
            repo = MarketSignalRepository(session)
            if fact_type:
                signals = repo.get_by_type(fact_type, days=30, limit=limit)
            else:
                signals = repo.get_recent(days=30, limit=limit)

        return [
            MemoryFact(
                fact_type=s.signal_type,
                content=s.title,
                confidence=1.0,
                metadata=s.metadata_json or {},
                created_at=s.occurred_at,
                source=s.source,
            )
            for s in signals
        ]

    def get_skill_trend(self, skill: str, days: int = 30) -> Dict[str, Any]:
        with db.session_scope() as session:
            return MarketSignalRepository(session).get_skill_trend(skill, days)

    def get_top_skills(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        with db.session_scope() as session:
            summary = MarketSignalRepository(session).get_market_summary(days)
        return summary.get("top_skills", [])[:limit]
