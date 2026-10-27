"""Resume domain events."""

from dataclasses import dataclass
from typing import Optional

from .event_types import Event


@dataclass
class ResumeGenerated(Event):
    """Target-aware resume generated."""

    user_id: str = ""
    resume_version: str = ""
    target_job_id: str = ""
    target_company: str = ""
    target_title: str = ""
    template_used: str = ""
    output_path: str = ""
    evidence_count: int = 0


@dataclass
class EvidenceAdded(Event):
    """New evidence added to Evidence Graph."""

    user_id: str = ""
    skill: str = ""
    project_name: str = ""
    confidence: float = 0.0
    evidence_type: str = "github_project"
    github_url: Optional[str] = None
    author_commits: int = 0
    stars: int = 0
