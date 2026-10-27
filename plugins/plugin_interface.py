"""Plugin interfaces for CareerOS extensions."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


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
                logger.warning("[%s] normalize failed: %s", name, exc)
        return result
