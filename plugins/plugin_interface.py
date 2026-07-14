"""Plugin interfaces for CareerOS extensions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ResumeData:
    """Structured resume data returned by any parser plugin."""

    # Scores (0–100)
    open_source: float
    self_projects: float
    production: float
    technical_skills: float
    total: float
    total_max: float

    # Extras
    bonus_points: float
    deductions: float
    total_work_experience: float
    total_education: float
    total_skills: int
    total_projects: int

    # GitHub
    github_repos: int
    github_followers: int
    github_following: int

    # Projects (from GitHub cache or equivalent)
    projects: List[Dict[str, Any]] = field(default_factory=list)

    # Raw CSV/API row — kept for enrichment payload extraction
    raw_scores: Dict[str, Any] = field(default_factory=dict)


class ResumeParserPlugin(ABC):
    """Abstract base class every resume parser plugin must implement."""

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return name, version, install_dir, enabled."""

    @abstractmethod
    def parse(self, pdf_path: Path, basename: str) -> ResumeData:
        """
        Parse resume PDF and return structured data.

        Args:
            pdf_path: Absolute path to PDF.
            basename: Stem of the PDF filename (used for cache lookups).
        """

    @abstractmethod
    def get_enrichment_payload(self, resume_data: ResumeData) -> Dict[str, Any]:
        """
        Extract fields to merge into career_scores.explanation["resume_score"].
        Which fields are returned is determined by config enrichment_keys.
        """
