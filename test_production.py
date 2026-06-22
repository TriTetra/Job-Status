"""
Production Integration Test: Real ApplyPilot data with Career OS
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from career_os.data.applypilot_loader import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import SemanticMatcher, GapAnalyzer, OpportunityScorer, CareerDecisionEngine


def test_load_real_data():
    """Test loading real ApplyPilot data."""
    print("=" * 70)
    print("TEST 1: Load Real Data from ApplyPilot")
    print("=" * 70)

    try:
        loader = ApplyPilotLoader()

        # Load jobs with score >= 7
        jobs = loader.load_jobs(min_score=7, limit=50)

        print(f"\n✓ Loaded {len(jobs)} jobs")

        if jobs:
            print("\nSample jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"\n{i}. {job.title} @ {job.company}")
                print(f"   Location: {job.location} ({'Remote' if job.remote else 'Onsite'})")
                print(f"   ApplyPilot Score: {job.fit_score}")
                print(f"   Required Skills: {', '.join(job.required_skills[:5])}")
                if job.salary_min:
                    print(f"   Salary: ${job.salary_min:,}")

        return jobs

    except FileNotFoundError as e:
        print(f"\n⚠️  {e}")
        print("Skipping real data tests - database not found")
        return []


def test_career_os_scoring(jobs):
    """Test Career OS scoring on real data."""
    if not jobs:
        print("\n⚠️  No jobs to score")
        return

    print("\n" + "=" * 70)
    print("TEST 2: Career OS Scoring vs ApplyPilot")
    print("=" * 70)

    # Initialize Career OS
    print("\nInitializing Career OS...")
    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    # Load user profile
    profile = create_user_profile_from_config()

    print(f"\nUser Profile:")
    print(f"  Name: {profile.name}")
    print(f"  Experience: {profile.years_experience} years")
    print(f"  Skills: {len(profile.skills)}")
    print(f"  AI Proficiency: {profile.ai_proficiency:.0%}")

    # Score jobs
    print(f"\nScoring {len(jobs)} jobs...")

    opportunities = scorer.rank_opportunities(jobs, profile)

    # Compare scores
    print("\n" + "-" * 70)
    print("Comparison: ApplyPilot Score vs Career OS Score")
    print("-" * 70)
    print(f"{'Title':<40} {'AP':<5} {'COS':<6} {'Acc%':<6} {'Rec':<15}")
    print("-" * 70)

    for opp in opportunities[:20]:  # Top 20
        ap_score = opp.job.fit_score or 0
        cos_score = opp.career_score
        acceptance = opp.acceptance_probability

        title = opp.job.title[:37] + "..." if len(opp.job.title) > 40 else opp.job.title

        print(f"{title:<40} {ap_score:<5.0f} {cos_score:5.1f}  {acceptance:5.1f}  {opp.recommendation[:15]}")

    # Statistics
    print("\n" + "-" * 70)
    print("Statistics:")
    print("-" * 70)

    ap_scores = [opp.job.fit_score for opp in opportunities if opp.job.fit_score]
    cos_scores = [opp.career_score for opp in opportunities]

    if ap_scores:
        print(f"ApplyPilot Scores:  avg={sum(ap_scores)/len(ap_scores):.1f}, "
              f"min={min(ap_scores):.0f}, max={max(ap_scores):.0f}")

    print(f"Career OS Scores:   avg={sum(cos_scores)/len(cos_scores):.1f}, "
          f"min={min(cos_scores):.1f}, max={max(cos_scores):.1f}")

    acceptance_rates = [opp.acceptance_probability for opp in opportunities]
    print(f"Acceptance Prob:    avg={sum(acceptance_rates)/len(acceptance_rates):.1f}%, "
          f"min={min(acceptance_rates):.1f}%, max={max(acceptance_rates):.1f}%")

    return opportunities


def test_full_analysis(jobs):
    """Test full career analysis."""
    if not jobs:
        return

    print("\n" + "=" * 70)
    print("TEST 3: Full Career Analysis")
    print("=" * 70)

    # Initialize
    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    profile = create_user_profile_from_config()

    # Full analysis
    result = engine.analyze_opportunities(jobs, profile, min_score=60.0)

    print("\n📊 CAREER ANALYSIS REPORT")
    print("=" * 70)

    print(f"\nTotal Jobs: {result['total_jobs']}")
    print(f"Viable (score >= 60): {result['viable_count']}")

    print(f"\n✅ APPLY NOW: {len(result['apply_now'])} jobs")
    for i, opp in enumerate(result['apply_now'][:10], 1):
        print(f"  {i}. {opp.job.title} @ {opp.job.company}")
        print(f"     Score: {opp.career_score:.1f} | Acceptance: {opp.acceptance_probability:.1f}% | EV: {opp.expected_value:.1f}")

    print(f"\n🤔 CONSIDER: {len(result['consider'])} jobs")
    for i, opp in enumerate(result['consider'][:5], 1):
        print(f"  {i}. {opp.job.title} @ {opp.job.company}")
        print(f"     {opp.recommendation}")

    if result['top_gaps']:
        print(f"\n📚 TOP SKILLS TO LEARN:")
        for gap in result['top_gaps']:
            print(f"  {gap.skill:15} | ROI: {gap.roi:5.2f} | Cost: {gap.learning_cost_hours:3}h | Impact: {gap.impact_score:.1f}")

    if result['learning_roadmap']:
        roadmap = result['learning_roadmap']
        print(f"\n🗓️  LEARNING ROADMAP: {roadmap.total_weeks} weeks ({roadmap.total_hours} hours)")
        for task in roadmap.tasks:
            print(f"  Week {task.start_week:2}: {task.skill} ({task.total_hours}h)")

    print("\n📈 STATISTICS:")
    print(f"  Avg Fit Score:      {result['stats']['avg_fit']:.1f}/100")
    print(f"  Avg Acceptance:     {result['stats']['avg_acceptance']:.1f}%")
    print(f"  Avg Career Score:   {result['stats']['avg_career_score']:.1f}/100")


def test_prioritization(opportunities):
    """Test application prioritization."""
    if not opportunities:
        return

    print("\n" + "=" * 70)
    print("TEST 4: Application Prioritization Strategy")
    print("=" * 70)

    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    # Prioritize top 15 applications
    prioritized = engine.prioritize_applications(opportunities, max_applications=15)

    print(f"\nPrioritized Top 15 Applications (from {len(opportunities)} opportunities):")
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
        print(f"  {size:12}: {count} applications ({count/15*100:.0f}%)")


def run_production_tests():
    """Run all production integration tests."""
    print("\n" + "=" * 70)
    print("  PRODUCTION INTEGRATION: Real ApplyPilot Data + Career OS")
    print("=" * 70)

    try:
        # Test 1: Load real data
        jobs = test_load_real_data()

        if not jobs:
            print("\n⚠️  Cannot run Career OS tests without jobs")
            print("Make sure ApplyPilot database exists at ~/.applypilot/applypilot.db")
            return

        # Test 2: Career OS scoring
        opportunities = test_career_os_scoring(jobs)

        # Test 3: Full analysis
        test_full_analysis(jobs)

        # Test 4: Prioritization
        if opportunities:
            test_prioritization(opportunities)

        print("\n" + "=" * 70)
        print("  ✓ PRODUCTION INTEGRATION COMPLETE")
        print("=" * 70)
        print("\nCareer OS successfully integrated with ApplyPilot!")
        print("Next: Use this for real job applications")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_production_tests()
