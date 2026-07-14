"""Job scoring service — orchestrates the scoring pipeline.

OpportunityScorer is cheap to instantiate (no model download), so it's
created eagerly. SemanticMatcher is only created when match() is needed
(via MatchingService lazy init).
"""

from datetime import datetime
from typing import Dict, List, Optional

from packages.db.connection import db
from packages.db.repositories import CareerScoreRepository
from packages.domain import Job, OpportunityScore, UserProfile
from packages.intelligence import OpportunityScorer


class ScoringService:
    """Orchestrates the job-scoring pipeline."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self._scorer = OpportunityScorer(matcher=None)

    def score_jobs(
        self,
        jobs: List[Job],
        profile: UserProfile,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[OpportunityScore]:
        """Score jobs without a semantic matcher (fast, no model load)."""
        return [self._scorer.score(job, profile, weights=weights) for job in jobs]

    def score_jobs_semantic(
        self,
        jobs: List[Job],
        profile: UserProfile,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[OpportunityScore]:
        """Score jobs with full semantic matching (triggers model download on first call)."""
        from packages.intelligence import SemanticMatcher
        if self._scorer.matcher is None:
            self._scorer.matcher = SemanticMatcher()
        return self.score_jobs(jobs, profile, weights=weights)

    def save_scores(
        self,
        scores: List[OpportunityScore],
        skill_gaps_map: Optional[Dict[str, List[str]]] = None,
        scanned_at: Optional[datetime] = None,
    ) -> int:
        """Persist OpportunityScore list to career_scores table."""
        skill_gaps_map = skill_gaps_map or {}
        scanned_at = scanned_at or datetime.utcnow()
        saved = 0

        with db.session_scope() as session:
            repo = CareerScoreRepository(session)
            for opp in scores:
                try:
                    gaps = skill_gaps_map.get(opp.job.url, [])
                    repo.save_score(
                        user_id=self.user_id,
                        url=opp.job.url,
                        scanned_at=scanned_at,
                        career_score=opp.career_score,
                        fit_score=opp.fit_score,
                        acceptance_probability=opp.acceptance_probability,
                        career_value=opp.career_value,
                        market_demand=opp.market_demand,
                        expected_value=opp.expected_value,
                        recommendation=opp.recommendation,
                        skill_gaps=gaps,
                        explanation={
                            "fit_score": opp.fit_score,
                            "acceptance_probability": opp.acceptance_probability,
                            "career_value": opp.career_value,
                            "market_demand": opp.market_demand,
                        },
                    )
                    saved += 1
                except Exception as e:
                    print(f"  [ScoringService] save failed for {opp.job.url}: {e}")

        return saved

    def run_pipeline(
        self,
        jobs: List[Job],
        profile: UserProfile,
        weights: Optional[Dict[str, float]] = None,
        semantic: bool = False,
    ) -> Dict:
        """Score + save + return summary dict."""
        scores = (
            self.score_jobs_semantic(jobs, profile, weights)
            if semantic
            else self.score_jobs(jobs, profile, weights)
        )
        saved = self.save_scores(scores)
        return {
            "total_jobs": len(jobs),
            "scored": len(scores),
            "saved_to_db": saved,
            "apply": sum(1 for s in scores if s.recommendation == "APPLY"),
            "consider": sum(1 for s in scores if s.recommendation == "CONSIDER"),
            "skip": sum(1 for s in scores if s.recommendation == "SKIP"),
        }
