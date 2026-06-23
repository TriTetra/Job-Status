"""
Production Integration Test: Real ApplyPilot data with Career OS

These tests hit the real ApplyPilot SQLite database at
~/.applypilot/applypilot.db and config.yaml at the project root. They are
skipped (not failed) when either is missing, since that's expected on a
machine that hasn't run a scan yet.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from career_os.data.applypilot_loader import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import SemanticMatcher, GapAnalyzer, OpportunityScorer, CareerDecisionEngine


@pytest.fixture(scope="module")
def real_jobs():
    """Load real jobs from the ApplyPilot database, skipping if unavailable."""
    try:
        loader = ApplyPilotLoader()
    except FileNotFoundError as e:
        pytest.skip(str(e))

    jobs = loader.load_jobs(min_score=7, limit=50)
    if not jobs:
        pytest.skip("ApplyPilot database has no jobs scored >= 7")
    return jobs


@pytest.fixture(scope="module")
def profile():
    """Load the real user profile from config.yaml, skipping if unavailable."""
    try:
        return create_user_profile_from_config()
    except FileNotFoundError as e:
        pytest.skip(str(e))


def test_load_real_data(real_jobs):
    """Test loading real ApplyPilot data."""
    print("=" * 70)
    print("TEST 1: Load Real Data from ApplyPilot")
    print("=" * 70)

    print(f"\nLoaded {len(real_jobs)} jobs")

    print("\nSample jobs:")
    for i, job in enumerate(real_jobs[:5], 1):
        print(f"\n{i}. {job.title} @ {job.company}")
        print(f"   Location: {job.location} ({'Remote' if job.remote else 'Onsite'})")
        print(f"   ApplyPilot Score: {job.fit_score}")
        print(f"   Required Skills: {', '.join(job.required_skills[:5])}")
        if job.salary_min:
            print(f"   Salary: ${job.salary_min:,}")

    assert len(real_jobs) > 0
    for job in real_jobs:
        assert job.title
        assert job.url
        # load_jobs(min_score=7) guarantees this filter at the query level
        assert job.fit_score is None or job.fit_score >= 7


def test_career_os_scoring(real_jobs, profile):
    """Test Career OS scoring on real data."""
    print("\n" + "=" * 70)
    print("TEST 2: Career OS Scoring vs ApplyPilot")
    print("=" * 70)

    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    scorer = OpportunityScorer(matcher=matcher)

    print(f"\nUser Profile:")
    print(f"  Name: {profile.name}")
    print(f"  Experience: {profile.years_experience} years")
    print(f"  Skills: {len(profile.skills)}")
    print(f"  AI Proficiency: {profile.ai_proficiency:.0%}")

    print(f"\nScoring {len(real_jobs)} jobs...")

    opportunities = scorer.rank_opportunities(real_jobs, profile)

    print("\n" + "-" * 70)
    print("Comparison: ApplyPilot Score vs Career OS Score")
    print("-" * 70)
    print(f"{'Title':<40} {'AP':<5} {'COS':<6} {'Acc%':<6} {'Rec':<15}")
    print("-" * 70)

    for opp in opportunities[:20]:
        ap_score = opp.job.fit_score or 0
        title = opp.job.title[:37] + "..." if len(opp.job.title) > 40 else opp.job.title
        print(f"{title:<40} {ap_score:<5.0f} {opp.career_score:5.1f}  "
              f"{opp.acceptance_probability:5.1f}  {opp.recommendation[:15]}")

    assert len(opportunities) == len(real_jobs)
    for opp in opportunities:
        assert 0.0 <= opp.career_score <= 100.0
        assert 0.0 <= opp.acceptance_probability <= 100.0

    # rank_opportunities must actually rank, not just pass through
    scores = [o.career_score for o in opportunities]
    assert scores == sorted(scores, reverse=True)


def test_full_analysis(real_jobs, profile):
    """Test full career analysis."""
    print("\n" + "=" * 70)
    print("TEST 3: Full Career Analysis")
    print("=" * 70)

    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    result = engine.analyze_opportunities(real_jobs, profile, min_score=60.0)

    print("\nCAREER ANALYSIS REPORT")
    print("=" * 70)

    print(f"\nTotal Jobs: {result['total_jobs']}")
    print(f"Viable (score >= 60): {result['viable_count']}")

    print(f"\nAPPLY NOW: {len(result['apply_now'])} jobs")
    for i, opp in enumerate(result['apply_now'][:10], 1):
        print(f"  {i}. {opp.job.title} @ {opp.job.company}")
        print(f"     Score: {opp.career_score:.1f} | Acceptance: {opp.acceptance_probability:.1f}% | EV: {opp.expected_value:.1f}")

    print(f"\nCONSIDER: {len(result['consider'])} jobs")
    for i, opp in enumerate(result['consider'][:5], 1):
        print(f"  {i}. {opp.job.title} @ {opp.job.company}")
        print(f"     {opp.recommendation}")

    if result['top_gaps']:
        print(f"\nTOP SKILLS TO LEARN:")
        for gap in result['top_gaps']:
            print(f"  {gap.skill:15} | ROI: {gap.roi:5.2f} | Cost: {gap.learning_cost_hours:3}h | Impact: {gap.impact_score:.1f}")

    if result['learning_roadmap']:
        roadmap = result['learning_roadmap']
        print(f"\nLEARNING ROADMAP: {roadmap.total_weeks} weeks ({roadmap.total_hours} hours)")
        for task in roadmap.tasks:
            print(f"  Week {task.start_week:2}: {task.skill} ({task.total_hours}h)")

    print("\nSTATISTICS:")
    print(f"  Avg Fit Score:      {result['stats']['avg_fit']:.1f}/100")
    print(f"  Avg Acceptance:     {result['stats']['avg_acceptance']:.1f}%")
    print(f"  Avg Career Score:   {result['stats']['avg_career_score']:.1f}/100")

    assert result["total_jobs"] == len(real_jobs)
    assert result["viable_count"] <= result["total_jobs"]
    assert len(result["apply_now"]) <= 10  # capped in analyze_opportunities
    assert len(result["consider"]) <= 10
    if result["learning_roadmap"]:
        assert result["learning_roadmap"].total_weeks <= 8


def test_prioritization(real_jobs, profile):
    """Test application prioritization."""
    print("\n" + "=" * 70)
    print("TEST 4: Application Prioritization Strategy")
    print("=" * 70)

    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, None, scorer)

    opportunities = scorer.rank_opportunities(real_jobs, profile)
    prioritized = engine.prioritize_applications(opportunities, max_applications=15)

    print(f"\nPrioritized Top {len(prioritized)} Applications (from {len(opportunities)} opportunities):")
    print("-" * 70)

    company_distribution = {}

    for i, opp in enumerate(prioritized, 1):
        size = opp.job.company_size
        company_distribution[size] = company_distribution.get(size, 0) + 1

        print(f"\n{i:2}. {opp.job.title}")
        print(f"    Company: {opp.job.company} ({size})")
        print(f"    Career Score: {opp.career_score:.1f} | EV: {opp.expected_value:.1f}")
        print(f"    Strategy: {opp.recommendation}")

    print("\n" + "-" * 70)
    print("Portfolio Diversification:")
    for size, count in company_distribution.items():
        print(f"  {size:12}: {count} applications ({count/len(prioritized)*100:.0f}%)")

    assert len(prioritized) <= 15
    assert {o.job.id for o in prioritized}.issubset({o.job.id for o in opportunities})


if __name__ == "__main__":
    try:
        loader = ApplyPilotLoader()
        jobs = loader.load_jobs(min_score=7, limit=50)
    except FileNotFoundError as e:
        print(f"\n{e}")
        print("Make sure ApplyPilot has been run at least once.")
        sys.exit(1)

    if not jobs:
        print("\nNo jobs found with score >= 7. Run an ApplyPilot scan first.")
        sys.exit(1)

    user_profile = create_user_profile_from_config()

    test_load_real_data(jobs)
    test_career_os_scoring(jobs, user_profile)
    test_full_analysis(jobs, user_profile)
    test_prioritization(jobs, user_profile)

    print("\n" + "=" * 70)
    print("  OK: PRODUCTION INTEGRATION COMPLETE")
    print("=" * 70)
