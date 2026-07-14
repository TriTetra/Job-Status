"""Company domain entity — pure Python, no DB dependency."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TechHub:
    city: str
    description: str = ""
    cost_of_living_index: int = 0
    major_companies: List[str] = field(default_factory=list)
    tech_stack_focus: List[str] = field(default_factory=list)


@dataclass
class Company:
    name: str
    tier: str = "unknown"
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    employee_count: Optional[int] = None

    tech_stack: List[str] = field(default_factory=list)

    hiring_trend: str = "stable"
    open_positions_count: int = 0
    sponsors_visa: bool = False
    remote_friendly: bool = True

    interview_rounds: List[dict] = field(default_factory=list)
    salary_ranges: Dict[str, Dict[str, dict]] = field(default_factory=dict)
    culture_signals: List[str] = field(default_factory=list)
    red_flags: List[dict] = field(default_factory=list)

    last_enriched: Optional[datetime] = None
    enrichment_source: Optional[str] = None

    def is_hiring(self) -> bool:
        return self.hiring_trend in ("up", "spike") and self.open_positions_count > 0

    def get_salary_range(self, role: str, level: str) -> Optional[dict]:
        return self.salary_ranges.get(role, {}).get(level)
