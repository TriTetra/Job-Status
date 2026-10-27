"""Job scoring service — orchestrates the scoring pipeline.

OpportunityScorer is cheap to instantiate (no model download), so it's
created eagerly. SemanticMatcher is only created when match() is needed
(via MatchingService lazy init).
"""

from datetime import datetime
from typing import Dict, List, Optional

from core.db.connection import db
from core.db.repositories import CareerScoreRepository
from core.domain import Job, OpportunityScore, UserProfile
from core.intelligence import OpportunityScorer
from .decision_builder import build_decision


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
        from core.intelligence import SemanticMatcher
        if self._scorer.matcher is None:
            self._scorer.matcher = SemanticMatcher()
        return self.score_jobs(jobs, profile, weights=weights)

    def _build_explanation(self, opp: OpportunityScore, profile: UserProfile) -> dict:
        job = opp.job
        matched_skills = []
        req_skills = job.required_skills or []
        for s in profile.skills:
            if any(s.name.lower() in req.lower() for req in req_skills):
                matched_skills.append({
                    "name": s.name,
                    "confidence": s.level.value if hasattr(s.level, 'value') else 0.7
                })

        highlights = []
        matched_skill_names = [m["name"] for m in matched_skills[:3]]
        if matched_skill_names:
            highlights.append(f"Strong match: {', '.join(matched_skill_names)}")
        if job.remote and profile.preferences and getattr(profile.preferences, 'remote', False):
            highlights.append("Remote work matches your preference")
        if opp.career_value and opp.career_value > 70:
            highlights.append("High career growth potential")
        if opp.market_demand and opp.market_demand > 60:
            highlights.append("In-demand role in current market")

        breakdown = [
            {
                "label": "Skill Match",
                "value": opp.fit_score,
                "positive": opp.fit_score >= 50,
                "description": "How well your skills match the job requirements"
            },
            {
                "label": "Career Value",
                "value": opp.career_value,
                "positive": opp.career_value >= 50,
                "description": "Long-term career growth potential"
            },
            {
                "label": "Market Demand",
                "value": opp.market_demand,
                "positive": opp.market_demand >= 50,
                "description": "How in-demand this role is in the market"
            },
            {
                "label": "Acceptance Probability",
                "value": opp.acceptance_probability,
                "positive": opp.acceptance_probability >= 20,
                "description": "Realistic chance of getting an offer"
            }
        ]

        return {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": job.remote,
            "description": job.description[:1000] if job.description else "",
            "required_skills": req_skills,
            "matched_skills": matched_skills[:5],
            "highlights": highlights,
            "breakdown": breakdown,
        }

    def save_scores(
        self,
        scores: List[OpportunityScore],
        skill_gaps_map: Optional[Dict[str, List[str]]] = None,
        scanned_at: Optional[datetime] = None,
        profile: Optional[UserProfile] = None,
        job_dicts: Optional[Dict[str, Dict]] = None,
        prefs: Optional[Dict] = None,
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
                    rec_normalized = opp.recommendation
                    if isinstance(rec_normalized, str) and " - " in rec_normalized:
                        rec_normalized = rec_normalized.split(" - ")[0].strip()

                    explanation = {
                        "fit_score": opp.fit_score,
                        "acceptance_probability": opp.acceptance_probability,
                        "career_value": opp.career_value,
                        "market_demand": opp.market_demand,
                    }
                    if profile:
                        explanation.update(self._build_explanation(opp, profile))

                    # ── Decision Contract v1 ──
                    job_meta_data = (job_dicts or {}).get(opp.job.url, {})
                    explanation["decision"] = build_decision(
                        recommendation=rec_normalized,
                        career_score=opp.career_score or 0,
                        career_value=opp.career_value or 0,
                        market_demand=opp.market_demand or 0,
                        job=job_meta_data,
                        prefs=prefs or {},
                        matched_skills=explanation.get("matched_skills", []),
                        gap_skills=gaps,
                    )

                    # Keep root level source/remote_region for UI backward compatibility
                    if job_meta_data.get("source") and job_meta_data["source"] != "unknown":
                        explanation["source"] = job_meta_data["source"]
                    if job_meta_data.get("remote_region"):
                        explanation["remote_region"] = job_meta_data["remote_region"]

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
                        recommendation=rec_normalized,
                        skill_gaps=gaps,
                        explanation=explanation,
                    )
                    saved += 1
                except Exception as e:
                    print(f"  [ScoringService] save failed for {opp.job.url}: {e}")

        return saved

    def _load_prefs(self) -> Dict:
        from core.db.repositories.career_preferences_repo import CareerPreferencesRepository
        try:
            with db.session_scope() as s:
                p = CareerPreferencesRepository(s).get_by_user_id(self.user_id)
                if not p:
                    return {}
                return {
                    "work_arrangements": p.work_arrangements or [],
                    "preferred_country_codes": p.preferred_country_codes or [],
                    "requires_sponsorship": p.requires_sponsorship,
                    "salary_min": p.salary_min,
                    "salary_max": p.salary_max,
                }
        except Exception:
            return {}

    def run_pipeline(
        self,
        jobs: List[Job],
        profile: UserProfile,
        weights: Optional[Dict[str, float]] = None,
        semantic: bool = False,
        job_meta: Optional[Dict[str, Dict]] = None,
    ) -> Dict:
        """Score + save + return summary dict."""
        prefs = self._load_prefs()
        job_dicts = {
            j.url: {
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "remote": j.remote,
                "remote_region": (job_meta or {}).get(j.url, {}).get("remote_region") if job_meta else None,
                "sponsors_visa": j.sponsors_visa,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "required_skills": j.required_skills or [],
                **((job_meta or {}).get(j.url) or {}),
            }
            for j in jobs
        }
        scores = (
            self.score_jobs_semantic(jobs, profile, weights)
            if semantic
            else self.score_jobs(jobs, profile, weights)
        )
        saved = self.save_scores(
            scores, profile=profile, job_dicts=job_dicts, prefs=prefs
        )

        def clean_rec(r):
            if isinstance(r, str) and " - " in r:
                return r.split(" - ")[0].strip()
            return r

        return {
            "total_jobs": len(jobs),
            "scored": len(scores),
            "saved_to_db": saved,
            "apply": sum(1 for s in scores if clean_rec(s.recommendation) == "APPLY"),
            "consider": sum(1 for s in scores if clean_rec(s.recommendation) == "CONSIDER"),
            "skip": sum(1 for s in scores if clean_rec(s.recommendation) == "SKIP"),
        }
