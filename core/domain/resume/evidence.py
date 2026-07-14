"""Evidence domain entity — skill proof."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Evidence:
    user_id: str
    skill_name: str
    project_name: str

    author_commits: int = 0
    stars: int = 0
    loc_count: Optional[int] = None

    confidence: float = 0.0

    github_url: Optional[str] = None
    evidence_type: str = "github_project"
    evaluation_scores: Dict[str, float] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_strong(self, threshold: float = 0.7) -> bool:
        return self.confidence >= threshold

    def get_display_summary(self) -> str:
        return f"{self.project_name}: {self.author_commits} commits, {self.stars} stars"
