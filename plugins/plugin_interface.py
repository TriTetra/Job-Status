"""Plugin interfaces for CareerOS extensions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


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


class JobSourcePlugin(ABC):
    """
    Abstract base class for job source plugins.

    Implementations: ApplyPilot, JobSpy, LinkedIn, Greenhouse, etc.
    """

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return name, version, description, enabled, job_count."""

    @abstractmethod
    def scan(self, hours_old: int = 72, min_score: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch raw jobs from the source.

        Args:
            hours_old: Only jobs discovered in last N hours.
            min_score: Minimum fit score threshold (0 = all).

        Returns:
            List of raw job dicts in source-specific schema.
        """

    @abstractmethod
    def normalize(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw job to the canonical Job schema:

            url, title, company, description, location, remote,
            required_skills, preferred_skills, required_years,
            salary_min, salary_max, company_size, sponsors_visa,
            posted_date, source, fit_score, application_url
        """

    def scan_and_normalize(
        self, hours_old: int = 72, min_score: int = 7
    ) -> List[Dict[str, Any]]:
        """Convenience: scan + normalize in one call."""
        raw_jobs = self.scan(hours_old=hours_old, min_score=min_score)
        result: List[Dict[str, Any]] = []
        name = self.get_metadata().get("name", "unknown")
        for raw in raw_jobs:
            try:
                result.append(self.normalize(raw))
            except Exception as exc:
                print(f"[{name}] normalize failed: {exc}")
        return result
