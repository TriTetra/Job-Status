"""Semantic matching service.

SemanticMatcher loads a 420MB embedding model — imported lazily so tests and
lightweight callers don't pay that cost unless they actually call match().
"""

from typing import List, Optional

from core.domain import Job, MatchResult, UserProfile


class MatchingService:
    """Semantic job-to-profile matching."""

    def __init__(self):
        self._matcher = None

    def _get_matcher(self):
        if self._matcher is None:
            from core.intelligence import SemanticMatcher
            self._matcher = SemanticMatcher()
        return self._matcher

    def match_job(self, job: Job, profile: UserProfile) -> MatchResult:
        """Match a single job to a user profile."""
        return self._get_matcher().match(profile, job)

    def match_jobs(self, jobs: List[Job], profile: UserProfile) -> List[MatchResult]:
        """Match a list of jobs against the user profile."""
        matcher = self._get_matcher()
        return [matcher.match(profile, j) for j in jobs]

    def get_top_matches(
        self,
        jobs: List[Job],
        profile: UserProfile,
        limit: int = 10,
    ) -> List[MatchResult]:
        """Return top N matches sorted by overall_score descending."""
        matches = self.match_jobs(jobs, profile)
        return sorted(matches, key=lambda m: m.overall_score, reverse=True)[:limit]
