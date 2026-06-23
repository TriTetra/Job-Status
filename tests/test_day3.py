"""
Test Day 3: Opportunity Scorer + Career Decision Engine
"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from career_os.models import Skill, SkillLevel, UserProfile, Job, UserPreferences, Experience
from career_os.intelligence import SemanticMatcher, GapAnalyzer
from career_os.intelligence.opportunity_scorer import OpportunityScorer, CareerDecisionEngine


def create_test_profile() -> UserProfile:
    """Create test profile."""
    return UserProfile(
        name="Test User",
        email="test@example.com",
        years_experience=2.5,
        ai_proficiency=0.8,
        skills=[
            Skill("Python", SkillLevel.INDEPENDENT, ai_multiplier=0.8),
            Skill("PyTorch", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("FastAPI", SkillLevel.WORKING, ai_multiplier=0.6),
            Skill("Docker", SkillLevel.WORKING, ai_multiplier=0.5),
            Skill("Machine Learning", SkillLevel.WORKING, ai_multiplier=0.7),
        ],
        target_roles=["ML Engineer", "Backend Engineer"],
        preferences=UserPreferences(
            remote=True,
            work_visa_required=True
        )
    )


def create_diverse_jobs() -> list[Job]:
    """Create diverse job scenarios."""
    return [
        # Scenario 1: Perfect match, startup, remote
        Job(
            id="1", title="ML Engineer", company="AI Startup", description="Build ML systems",
            url="https://example.com/1", location="Remote", remote=True,
            required_skills=["Python", "PyTorch", "Docker"], required_years=2.0,
            salary_min=120000, salary_max=160000, company_size="startup", sponsors_visa=True
        ),
        # Scenario 2: Google - high value, low acceptance
        Job(
            id="2", title="ML Engineer", company="Google", description="ML infrastructure",
            url="https://example.com/2", location="Mountain View", remote=False,
            required_skills=["Python", "TensorFlow", "Kubernetes", "AWS"], required_years=3.0,
            salary_min=180000, salary_max=250000, company_size="big_tech", sponsors_visa=True
        ),
        # Scenario 3: Senior role - overreach
        Job(
            id="3", title="Senior ML Engineer", company="Tech Corp", description="Lead ML team",
            url="https://example.com/3", location="Remote", remote=True,
            required_skills=["Python", "PyTorch", "Kubernetes", "MLOps"], required_years=5.0,
            salary_min=160000, salary_max=200000, company_size="large", sponsors_visa=False
        ),
        # Scenario 4: Backend - adjacent role
        Job(
            id="4", title="Backend Engineer", company="Startup", description="Build APIs",
            url="https://example.com/4", location="Remote", remote=True,
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"], required_years=2.0,
            salary_min=110000, salary_max=150000, company_size="midsize", sponsors_visa=True
        ),
        # Scenario 5: Junior role - underqualified position
        Job(
            id="5", title="Junior ML Engineer", company="Corp", description="Entry level",
            url="https://example.com/5", location="Remote", remote=True,
            required_skills=["Python", "Machine Learning"], required_years=0.5,
            salary_min=80000, salary_max=100000, company_size="large", sponsors_visa=False
        ),
    ]


def test_opportunity_scorer():
    """Test opportunity scoring."""
    print("=" * 70)
    print("TEST 1: Opportunity Scorer")
    print("=" * 70)

    scorer = OpportunityScorer()
    profile = create_test_profile()
    jobs = create_diverse_jobs()

    print(f"\nScoring {len(jobs)} opportunities...")
    print("\n" + "-" * 70)

    scores = {}
    for job in jobs:
        score = scorer.score(job, profile)
        scores[job.id] = score

        print(f"\n{job.title} at {job.company}")
        print(f"  Company: {job.company_size:10} | Remote: {job.remote}")
        print(f"  Salary: {job.salary_min:,} - {job.salary_max:,}")
        print(f"\n  Scores:")
        print(f"    Fit:             {score.fit_score:5.1f}/100")
        print(f"    Acceptance:      {score.acceptance_probability:5.1f}/100")
        print(f"    Career Value:    {score.career_value:5.1f}/100")
        print(f"    Market Demand:   {score.market_demand:5.1f}/100")
        print(f"\n    Career Score:    {score.career_score:5.1f}/100")
        print(f"    Expected Value:  {score.expected_value:5.1f}/100")
        print(f"\n  -> {score.recommendation}")
        print("-" * 70)

        # Every score component is a bounded percentage
        assert 0.0 <= score.fit_score <= 100.0
        assert 0.0 <= score.acceptance_probability <= 100.0
        assert 0.0 <= score.career_value <= 100.0
        assert score.recommendation

    # Exact skill match (job 1) scores a perfect fit
    assert scores["1"].fit_score == pytest.approx(100.0)
    # Startups carry a higher acceptance multiplier than big tech in this model
    assert scores["1"].acceptance_probability > scores["2"].acceptance_probability
    # Visa required but not sponsored should depress acceptance vs. sponsored roles
    assert scores["3"].acceptance_probability < scores["1"].acceptance_probability

    print("\nOK: Opportunity scorer working\n")


def test_ranking():
    """Test opportunity ranking."""
    print("=" * 70)
    print("TEST 2: Opportunity Ranking")
    print("=" * 70)

    scorer = OpportunityScorer()
    profile = create_test_profile()
    jobs = create_diverse_jobs()

    ranked = scorer.rank_opportunities(jobs, profile)

    print("\nRanked by Career Score:")
    print("-" * 70)
    print(f"{'Rank':<6} {'Job':<30} {'Score':<8} {'EV':<8} {'Rec':<30}")
    print("-" * 70)

    for i, opp in enumerate(ranked, 1):
        print(f"{i:<6} {opp.job.title + ' @' + opp.job.company:<30} "
              f"{opp.career_score:6.1f}   {opp.expected_value:6.1f}   {opp.recommendation}")

    # Ranking must actually be sorted by career_score, descending
    scores = [o.career_score for o in ranked]
    assert scores == sorted(scores, reverse=True)
    assert len(ranked) == len(jobs)
    assert {o.job.id for o in ranked} == {j.id for j in jobs}

    print("\nOK: Ranking working\n")


def test_acceptance_factors():
    """Test acceptance probability factors."""
    print("=" * 70)
    print("TEST 3: Acceptance Probability Breakdown")
    print("=" * 70)

    scorer = OpportunityScorer()
    profile = create_test_profile()

    # Test different scenarios
    scenarios = [
        ("Startup, exact exp, remote, visa", Job(
            id="1", title="ML Engineer", company="Startup", description="ML",
            url="x", location="Remote", remote=True, required_years=2.5,
            company_size="startup", sponsors_visa=True, required_skills=["Python"]
        )),
        ("Google, exact exp, onsite, visa", Job(
            id="2", title="ML Engineer", company="Google", description="ML",
            url="x", location="SF", remote=False, required_years=2.5,
            company_size="big_tech", sponsors_visa=True, required_skills=["Python"]
        )),
        ("Startup, under-exp, remote, no visa", Job(
            id="3", title="Senior ML", company="Startup", description="ML",
            url="x", location="Remote", remote=True, required_years=5.0,
            company_size="startup", sponsors_visa=False, required_skills=["Python"]
        )),
    ]

    print("\nAcceptance probability by scenario:")
    print("-" * 70)

    acceptance = {}
    for desc, job in scenarios:
        score = scorer.score(job, profile)
        acceptance[desc] = score.acceptance_probability
        print(f"{desc:50} -> {score.acceptance_probability:5.1f}%")

    # A startup with an exact experience match and remote+visa fit should
    # have a meaningfully higher acceptance probability than the same
    # candidate applying to Google onsite
    startup_exact = acceptance["Startup, exact exp, remote, visa"]
    google_exact = acceptance["Google, exact exp, onsite, visa"]
    assert startup_exact > google_exact

    print("\nOK: Acceptance factors working\n")


def test_career_decision_engine():
    """Test full decision engine."""
    print("=" * 70)
    print("TEST 4: Career Decision Engine")
    print("=" * 70)

    print("\nInitializing components...")
    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)

    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    profile = create_test_profile()
    jobs = create_diverse_jobs()

    print(f"Analyzing {len(jobs)} opportunities...\n")

    result = engine.analyze_opportunities(jobs, profile, min_score=50.0)

    print("=" * 70)
    print("  CAREER ANALYSIS REPORT")
    print("=" * 70)

    print(f"\nTotal Jobs Analyzed: {result['total_jobs']}")
    print(f"Viable Opportunities (score >= 50): {result['viable_count']}")

    print(f"\nStatistics:")
    print(f"  Average Fit Score:      {result['stats']['avg_fit']:.1f}/100")
    print(f"  Average Acceptance:     {result['stats']['avg_acceptance']:.1f}%")
    print(f"  Average Career Score:   {result['stats']['avg_career_score']:.1f}/100")

    print(f"\nAPPLY NOW ({len(result['apply_now'])}):")
    print("-" * 70)
    for opp in result['apply_now'][:5]:
        print(f"  {opp.job.title} @ {opp.job.company}")
        print(f"    Score: {opp.career_score:.1f} | Acceptance: {opp.acceptance_probability:.1f}% | EV: {opp.expected_value:.1f}")

    print(f"\nCONSIDER ({len(result['consider'])}):")
    print("-" * 70)
    for opp in result['consider'][:3]:
        print(f"  {opp.job.title} @ {opp.job.company}")
        print(f"    Score: {opp.career_score:.1f} | {opp.recommendation}")

    if result['top_gaps']:
        print(f"\nTOP SKILLS TO LEARN ({len(result['top_gaps'])}):")
        print("-" * 70)
        for gap in result['top_gaps']:
            print(f"  {gap.skill:15} | ROI: {gap.roi:5.2f} | Cost: {gap.learning_cost_hours:3}h | Jobs: {gap.jobs_unlocked}")

    if result['learning_roadmap']:
        roadmap = result['learning_roadmap']
        print(f"\nLEARNING ROADMAP:")
        print("-" * 70)
        print(f"  Duration: {roadmap.total_weeks} weeks ({roadmap.total_hours} hours)")
        print(f"  Expected improvement: +{roadmap.expected_fit_improvement:.0f}% fit score")
        print(f"\n  Schedule:")
        for task in roadmap.tasks:
            print(f"    Week {task.start_week:2}: {task.skill} ({task.total_hours}h)")

    print("\n" + "=" * 70)

    assert result["total_jobs"] == len(jobs)
    assert result["viable_count"] <= result["total_jobs"]
    # apply_now and consider are mutually exclusive subsets of the viable jobs
    apply_ids = {o.job.id for o in result["apply_now"]}
    consider_ids = {o.job.id for o in result["consider"]}
    assert apply_ids.isdisjoint(consider_ids)
    assert len(apply_ids) + len(consider_ids) <= result["viable_count"]

    print("\nOK: Career decision engine working\n")


def test_prioritization():
    """Test application prioritization."""
    print("=" * 70)
    print("TEST 5: Application Prioritization")
    print("=" * 70)

    scorer = OpportunityScorer()
    engine = CareerDecisionEngine(None, None, scorer)

    profile = create_test_profile()
    jobs = create_diverse_jobs()

    # Score all
    opportunities = scorer.rank_opportunities(jobs, profile)

    # Prioritize
    prioritized = engine.prioritize_applications(opportunities, max_applications=3)

    print(f"\nFrom {len(opportunities)} opportunities, prioritizing top 3:")
    print("-" * 70)

    for i, opp in enumerate(prioritized, 1):
        print(f"\n{i}. {opp.job.title} @ {opp.job.company}")
        print(f"   Career Score: {opp.career_score:.1f}")
        print(f"   Expected Value: {opp.expected_value:.1f}")
        print(f"   Strategy: {opp.recommendation}")

    assert len(prioritized) == 3
    # Prioritization respects the max_applications cap and pulls from the
    # scored pool, never inventing opportunities
    assert {o.job.id for o in prioritized}.issubset({o.job.id for o in opportunities})

    print("\nOK: Prioritization working\n")


if __name__ == "__main__":
    test_opportunity_scorer()
    test_ranking()
    test_acceptance_factors()
    test_prioritization()
    test_career_decision_engine()
    print("=" * 70)
    print("  OK: ALL DAY 3 TESTS PASSED")
    print("=" * 70)
