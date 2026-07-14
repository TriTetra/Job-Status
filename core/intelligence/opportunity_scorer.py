"""
Opportunity scoring with acceptance probability and career value.
"""

from typing import List, Dict, Optional
import numpy as np

from core.domain import UserProfile, Job, OpportunityScore


class OpportunityScorer:
    """
    Evaluate job opportunities across multiple dimensions.

    Calculates:
    1. Fit score (how well you match)
    2. Acceptance probability (chance of getting the job)
    3. Career value (long-term benefit)
    4. Market demand (skill market value)
    5. Career score (weighted combination)
    6. Expected value (fit × acceptance × career)
    """

    def __init__(self, matcher=None):
        """
        Initialize scorer.

        Args:
            matcher: Optional SemanticMatcher instance (for fit scores)
        """
        self.matcher = matcher

        # Company tier data (for acceptance probability)
        self.company_tiers = self._build_company_tiers()

        # Market demand data (could be real-time in production)
        self.skill_demand = self._build_demand_data()

    def score(
        self,
        job: Job,
        user: UserProfile,
        weights: Optional[Dict[str, float]] = None,
    ) -> OpportunityScore:
        """
        Calculate comprehensive opportunity score.

        Args:
            job: Job posting
            user: User profile
            weights: Optional per-user scoring weights dict with keys
                     fit, acceptance, career_value, market_demand.
                     Falls back to hardcoded defaults if not supplied.

        Returns:
            OpportunityScore with all metrics
        """

        # Component 1: Fit Score (from semantic matcher)
        if self.matcher:
            match_result = self.matcher.match(user, job)
            fit = match_result.overall_score / 100
        else:
            # Fallback: simple skill overlap
            fit = self._simple_fit(user, job)

        # Component 2: Acceptance Probability
        acceptance = self._estimate_acceptance(job, user)

        # Component 3: Career Value
        career_value = self._calculate_career_value(job, user)

        # Component 4: Market Demand
        market = self._calculate_market_demand(job)

        # Per-user weights (or hardcoded defaults)
        w = weights or {}
        w_fit = float(w.get("fit", 0.30))
        w_acc = float(w.get("acceptance", 0.25))
        w_cv = float(w.get("career_value", 0.25))
        w_mkt = float(w.get("market_demand", 0.20))

        career_score = (
            w_fit * fit +
            w_acc * acceptance +
            w_cv * career_value +
            w_mkt * market
        ) * 100

        # Expected Value (product of probabilities)
        expected_value = fit * acceptance * career_value * 100

        # Recommendation
        recommendation = self._generate_recommendation(
            career_score, acceptance, fit
        )

        return OpportunityScore(
            job=job,
            fit_score=fit * 100,
            acceptance_probability=acceptance * 100,
            career_value=career_value * 100,
            market_demand=market * 100,
            career_score=career_score,
            expected_value=expected_value,
            recommendation=recommendation
        )

    def rank_opportunities(
        self,
        jobs: List[Job],
        user: UserProfile,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[OpportunityScore]:
        """
        Score and rank all opportunities.

        Args:
            jobs: List of job postings
            user: User profile
            weights: Optional per-user scoring weights (passed through to score())

        Returns:
            List of OpportunityScore sorted by career_score (descending)
        """
        scores = [self.score(job, user, weights=weights) for job in jobs]
        return sorted(scores, key=lambda s: s.career_score, reverse=True)

    def _estimate_acceptance(self, job: Job, user: UserProfile) -> float:
        """
        Estimate probability of getting the job.

        Factors:
        - Company size/tier (big tech = harder)
        - Experience gap (under/over qualified)
        - Remote availability (boosts chances)
        - Visa sponsorship (penalty if needed but not offered)
        - Competition estimate (based on job attractiveness)

        Returns:
            Probability 0.0-1.0
        """

        # Start with baseline
        prob = 0.5

        # Factor 1: Company size
        company_factor = self._company_acceptance_factor(job.company_size)
        prob *= company_factor

        # Factor 2: Experience gap
        exp_factor = self._experience_factor(job.required_years, user.years_experience)
        prob *= exp_factor

        # Factor 3: Remote advantage
        if job.remote and user.preferences.remote:
            prob *= 1.3  # 30% boost for remote match
        elif not job.remote and not user.preferences.onsite_acceptable:
            prob *= 0.3  # Major penalty for location mismatch

        # Factor 4: Visa sponsorship
        if user.preferences.work_visa_required:
            if job.sponsors_visa:
                prob *= 0.9  # Slight penalty (still harder)
            else:
                prob *= 0.4  # Major penalty (possible but unlikely)

        # Factor 5: Competition estimate
        competition = self._estimate_competition(job)
        prob *= competition

        # Factor 6: Seniority mismatch
        if "senior" in job.title.lower() and user.years_experience < 5:
            prob *= 0.6  # Harder to get senior roles early
        elif "junior" in job.title.lower() and user.years_experience > 4:
            prob *= 0.7  # Overqualified penalty

        # Cap at realistic maximum
        return min(prob, 0.95)

    def _company_acceptance_factor(self, company_size: str) -> float:
        """
        Acceptance factor by company size.

        Args:
            company_size: startup, midsize, large, big_tech

        Returns:
            Multiplier 0.0-1.0
        """
        factors = {
            "big_tech": 0.25,     # FAANG/top tier - very hard
            "large": 0.45,        # Large companies - hard
            "midsize": 0.7,       # Mid-size - moderate
            "startup": 1.2,       # Startups - easier, desperate
            "unknown": 0.6        # Default
        }

        return factors.get(company_size.lower(), 0.6)

    def _experience_factor(self, required: float, actual: float) -> float:
        """
        Factor based on experience gap.

        Perfect match = 1.0
        Under-qualified = exponential decay
        Over-qualified = slight penalty

        Args:
            required: Required years
            actual: User's years

        Returns:
            Multiplier 0.0-1.0
        """
        if required == 0:
            return 1.0

        ratio = actual / required

        if 0.8 <= ratio <= 1.5:
            # Close match
            return 1.0
        elif ratio > 1.5:
            # Overqualified
            if ratio > 3:
                return 0.5  # Way overqualified
            return 0.8
        else:
            # Under-qualified - exponential decay
            # 0.5x = 0.5, 0.7x = 0.7, etc
            return ratio ** 1.5

    def _estimate_competition(self, job: Job) -> float:
        """
        Estimate competition level.

        High competition = low probability

        Factors:
        - Remote jobs (more applicants)
        - High salary (more applicants)
        - Prestigious company (more applicants)
        - Popular tech stack (more applicants)

        Returns:
            Multiplier 0.3-1.0
        """
        competition = 1.0

        # Remote = more competition
        if job.remote:
            competition *= 0.7

        # High salary = more competition
        if job.salary_min and job.salary_min > 150000:
            competition *= 0.7
        elif job.salary_min and job.salary_min > 200000:
            competition *= 0.5

        # Big tech = intense competition
        if job.company_size == "big_tech":
            competition *= 0.5

        # Popular stack = more applicants
        popular_skills = {"Python", "React", "JavaScript", "AWS"}
        if any(skill in popular_skills for skill in job.required_skills):
            competition *= 0.9

        return max(competition, 0.3)

    def _calculate_career_value(self, job: Job, user: UserProfile) -> float:
        """
        Long-term career value of this opportunity.

        Factors:
        - Skill development (new skills to learn)
        - Salary growth potential
        - Company prestige/resume value
        - Industry alignment with goals
        - Role progression opportunity

        Returns:
            Score 0.0-1.0
        """
        value = 0.5  # Baseline

        # Factor 1: Skill development
        # More missing skills = more growth potential
        user_skills = {s.name.lower() for s in user.skills}
        required = {s.lower() for s in job.required_skills}
        missing = required - user_skills

        if missing:
            skill_growth = min(len(missing) / 5, 0.3)  # Up to +0.3
            value += skill_growth

        # Factor 2: Salary
        if job.salary_min:
            # Normalize to 0-0.3 scale (100k = 0, 300k = 0.3)
            salary_score = min((job.salary_min - 100000) / 666666, 0.3)
            value += max(salary_score, 0)

        # Factor 3: Company prestige
        prestige = {
            "big_tech": 0.2,
            "large": 0.1,
            "midsize": 0.05,
            "startup": 0.0  # Risky but growth
        }
        value += prestige.get(job.company_size, 0)

        # Factor 4: Target role alignment
        if any(target.lower() in job.title.lower() for target in user.target_roles):
            value += 0.1

        # Factor 5: Growth trajectory
        if "senior" in job.title.lower() and user.years_experience < 5:
            value += 0.1  # Career progression

        # Cap at 1.0
        return min(value, 1.0)

    def _calculate_market_demand(self, job: Job) -> float:
        """
        Market demand for this role's skills.

        Uses skill demand database (could be real-time in production)

        Returns:
            Score 0.0-1.0
        """
        if not job.required_skills:
            return 0.5

        # Get demand scores for each skill
        skill_scores = []
        for skill in job.required_skills:
            demand = self.skill_demand.get(skill.lower(), 0.5)
            skill_scores.append(demand)

        # Average demand
        return np.mean(skill_scores)

    def _simple_fit(self, user: UserProfile, job: Job) -> float:
        """
        Simple skill overlap (fallback if no matcher).

        Args:
            user: User profile
            job: Job posting

        Returns:
            Fit score 0.0-1.0
        """
        if not job.required_skills:
            return 0.5

        user_skills = {s.name.lower() for s in user.skills}
        required = [s.lower() for s in job.required_skills]

        matched = sum(1 for s in required if s in user_skills)

        return matched / len(required)

    def _generate_recommendation(self,
                                 career_score: float,
                                 acceptance: float,
                                 fit: float) -> str:
        """
        Generate application recommendation.

        Thresholds are calibrated for a visa-sponsorship-required candidate
        (acceptance probability structurally ~0.10-0.25 due to sponsorship
        penalty), so APPLY bars are set lower than a no-sponsorship baseline.

        Args:
            career_score: Overall career score (0-100)
            acceptance: Acceptance probability (0.0-1.0)
            fit: Fit score (0.0-1.0)

        Returns:
            Recommendation string
        """
        if career_score < 40 or acceptance < 0.05:
            return "SKIP - Better opportunities available"

        if career_score >= 65 and acceptance >= 0.15:
            return "APPLY - Strong opportunity"

        if career_score >= 55 and acceptance >= 0.10:
            return "APPLY - Good fit"

        if career_score >= 50 and acceptance >= 0.08:
            return "CONSIDER - Review details"

        if career_score >= 45:
            return "CONSIDER - Build skills first"

        return "SKIP - Better opportunities available"

    def _build_company_tiers(self) -> Dict[str, str]:
        """Build company tier database."""
        return {
            # Big Tech
            "google": "big_tech",
            "meta": "big_tech",
            "amazon": "big_tech",
            "apple": "big_tech",
            "microsoft": "big_tech",
            "netflix": "big_tech",

            # Unicorns
            "openai": "big_tech",
            "anthropic": "big_tech",
            "databricks": "large",
            "stripe": "large",
        }

    def _build_demand_data(self) -> Dict[str, float]:
        """
        Build skill demand database.

        In production, this would be real-time market data.

        Returns:
            Dict of {skill: demand_score} (0-1)
        """
        return {
            # Very high demand
            "python": 0.95,
            "aws": 0.9,
            "kubernetes": 0.85,
            "react": 0.85,
            "docker": 0.85,
            "llm": 0.9,
            "machine learning": 0.9,

            # High demand
            "pytorch": 0.8,
            "fastapi": 0.75,
            "postgresql": 0.75,
            "typescript": 0.8,
            "go": 0.75,

            # Moderate demand
            "rust": 0.6,
            "scala": 0.5,
            "terraform": 0.7,

            # Lower demand
            "php": 0.4,
            "perl": 0.3,
        }


class CareerDecisionEngine:
    """
    High-level decision engine combining all intelligence.

    Orchestrates:
    - Semantic matching (fit)
    - Gap analysis (what to learn)
    - Opportunity scoring (what to apply)
    """

    def __init__(self, matcher, analyzer, scorer):
        """
        Initialize engine.

        Args:
            matcher: SemanticMatcher instance
            analyzer: GapAnalyzer instance
            scorer: OpportunityScorer instance
        """
        self.matcher = matcher
        self.analyzer = analyzer
        self.scorer = scorer

    def analyze_opportunities(self,
                             jobs: List[Job],
                             user: UserProfile,
                             min_score: float = 50.0) -> Dict:
        """
        Full analysis pipeline.

        Args:
            jobs: All available jobs
            user: User profile
            min_score: Minimum career score threshold

        Returns:
            Dict with recommendations, gaps, and priorities
        """

        # Step 1: Score all opportunities
        opportunities = self.scorer.rank_opportunities(jobs, user)

        # Step 2: Filter by threshold
        viable = [opp for opp in opportunities if opp.career_score >= min_score]

        # Step 3: Categorize by recommendation
        apply_now = [opp for opp in viable if "APPLY" in opp.recommendation]
        consider = [opp for opp in viable if "CONSIDER" in opp.recommendation]

        # Step 4: Analyze gaps for viable jobs
        viable_jobs = [opp.job for opp in viable]
        gaps = self.analyzer.analyze(user, viable_jobs) if viable_jobs else []

        # Step 5: Generate roadmap
        roadmap = self.analyzer.create_roadmap(gaps[:5]) if gaps else None

        return {
            "total_jobs": len(jobs),
            "viable_count": len(viable),
            "apply_now": apply_now[:10],  # Top 10
            "consider": consider[:10],
            "top_gaps": gaps[:5],
            "learning_roadmap": roadmap,
            "stats": {
                "avg_fit": np.mean([o.fit_score for o in viable]) if viable else 0,
                "avg_acceptance": np.mean([o.acceptance_probability for o in viable]) if viable else 0,
                "avg_career_score": np.mean([o.career_score for o in viable]) if viable else 0,
            }
        }

    def prioritize_applications(self,
                                opportunities: List[OpportunityScore],
                                max_applications: int = 20) -> List[OpportunityScore]:
        """
        Prioritize which jobs to apply to.

        Strategy:
        - Top expected value opportunities
        - Diversify by company size
        - Balance reach/target/safety

        Args:
            opportunities: All scored opportunities
            max_applications: Maximum to apply to

        Returns:
            Prioritized list
        """

        # Sort by expected value
        sorted_opps = sorted(opportunities, key=lambda o: o.expected_value, reverse=True)

        selected = []
        company_sizes = {"big_tech": 0, "large": 0, "midsize": 0, "startup": 0}

        for opp in sorted_opps:
            if len(selected) >= max_applications:
                break

            # Diversification: don't over-apply to one tier
            size = opp.job.company_size
            if company_sizes.get(size, 0) >= max_applications // 3:
                continue

            selected.append(opp)
            company_sizes[size] = company_sizes.get(size, 0) + 1

        return selected
