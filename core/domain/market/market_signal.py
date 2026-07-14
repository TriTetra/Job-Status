"""Market signal domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class MarketSignal:
    signal_type: str
    source: str
    title: str
    occurred_at: datetime

    impact: str = "medium"

    companies_affected: List[str] = field(default_factory=list)
    skills_affected: List[str] = field(default_factory=list)
    countries_affected: List[str] = field(default_factory=list)

    magnitude: Optional[float] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    source_id: Optional[str] = None

    def is_high_impact(self) -> bool:
        return self.impact in ("high", "critical")
