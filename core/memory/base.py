"""Base memory abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryFact:
    fact_type: str
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    source: str = "unknown"

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "fact_type": self.fact_type,
            "content": self.content,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "source": self.source,
        }


class BaseMemory(ABC):
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    @abstractmethod
    def add_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        expires_after_days: Optional[int] = None,
    ) -> MemoryFact:
        pass

    @abstractmethod
    def get_facts(
        self,
        fact_type: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[MemoryFact]:
        pass

    def search(self, query: str, limit: int = 10) -> List[MemoryFact]:
        """Simple substring search — future: vector similarity."""
        facts = self.get_facts(limit=1000)
        q = query.lower()
        return [f for f in facts if q in f.content.lower()][:limit]

    def clear(self):
        pass

    def get_summary(self) -> str:
        facts = self.get_facts(limit=20)
        if not facts:
            return "No memories yet."
        lines = [f"Memory Summary ({len(facts)} facts):"]
        for fact in facts[:10]:
            lines.append(f"  - [{fact.fact_type}] {fact.content}")
        if len(facts) > 10:
            lines.append(f"  ... and {len(facts) - 10} more")
        return "\n".join(lines)
