"""
Test Day 2: Semantic Matcher + Gap Analyzer
"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from career_os.models import Skill, SkillLevel, UserProfile, Job, Experience, UserPreferences
from career_os.intelligence import SemanticMatcher, GapAnalyzer


def create_test_profile() -> UserProfile:
    """Create realistic user profile."""
    return UserProfile(
        name="Abdullokh Abdukodirov",
        email="test@example.com",
        years_experience=2.0,
        ai_proficiency=0.8,
        skills=[
            Skill("Python", SkillLevel.INDEPENDENT, ai_multiplier=0.8,
                  evidence=["YOLOv8 system with 92% mAP", "FastAPI production apps"]),
            Skill("PyTorch", SkillLevel.WORKING, ai_multiplier=0.7,
                  evidence=["Computer vision models"]),
            Skill("Computer Vision", SkillLevel.WORKING, ai_multiplier=0.7,
                  evidence=["YOLOv8 deployment"]),
            Skill("FastAPI", SkillLevel.WORKING, ai_multiplier=0.6,
                  evidence=["REST APIs in production"]),
            Skill("Docker", SkillLevel.WORKING, ai_multiplier=0.5,
                  evidence=["Containerized ML apps"]),
            Skill("Machine Learning", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("AWS", SkillLevel.AI_ASSISTED, ai_multiplier=0.4),
            Skill("React", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),
        ],
        experience=[
            Experience(
                title="ML Engineer",
                company="KOU STORM UAV",
                description="Built YOLOv8 object detection achieving 92% mAP on edge devices",
                start_date=datetime(2023, 1, 1),
                achievements=[
                    "Optimized inference to 40ms latency",
                    "Deployed on Raspberry Pi 5"
                ]
            )
        ],
        target_roles=["ML Engineer", "AI Engineer", "Backend Engineer"],
        resume_text="ML Engineer with 2 years experience in computer vision and deep learning",
        preferences=UserPreferences(
            remote=True,
            work_visa_required=True
        )
    )


def create_test_jobs() -> list[Job]:
    """Create test job postings."""
    return [
        Job(
            id="job-1",
            title="ML Engineer",
            company="Acme AI",
            description="Build ML systems with PyTorch and deploy to AWS. Work on computer vision and LLM projects.",
            url="https://example.com/1",
            location="Remote",
            remote=True,
            required_skills=["Python", "PyTorch", "AWS", "Docker"],
            preferred_skills=["Kubernetes", "Computer Vision"],
            required_years=2.0,
            salary_min=120000,
            salary_max=160000,
            company_size="startup"
        ),
        Job(
            id="job-2",
            title="Senior ML Engineer",
            company="Big Tech Corp",
            description="Lead ML infrastructure team",
            url="https://example.com/2",
            location="San Francisco",
            remote=False,
            required_skills=["Python", "TensorFlow", "Kubernetes", "AWS"],
            required_years=5.0,
            salary_min=200000,
            salary_max=280000,
            company_size="big_tech"
        ),
        Job(
            id="job-3",
            title="Backend Engineer",
            company="Startup XYZ",
            description="Build scalable APIs with FastAPI and PostgreSQL",
            url="https://example.com/3",
            location="Remote",
            remote=True,
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            preferred_skills=["AWS", "Redis"],
            required_years=2.0,
            salary_min=100000,
            salary_max=140000,
            company_size="startup"
        ),
    ]


@pytest.fixture(scope="module")
def matcher():
    return SemanticMatcher(model_name='all-MiniLM-L6-v2')  # Faster model


def test_semantic_matcher(matcher):
    """Test semantic matching."""
    print("=" * 70)
    print("TEST 1: Semantic Matcher")
    print("=" * 70)

    profile = create_test_profile()
    jobs = create_test_jobs()

    print(f"\nUser: {profile.name}")
    print(f"Skills: {len(profile.skills)}")
    print(f"Years: {profile.years_experience}")
    print(f"AI Proficiency: {profile.ai_proficiency:.0%}")

    print("\n" + "-" * 70)
    print("Matching Results:")
    print("-" * 70)

    results = {}
    for job in jobs:
        result = matcher.match(profile, job)
        results[job.id] = result

        print(f"\nJob: {job.title} at {job.company}")
        print(f"  Overall Score: {result.overall_score:.1f}/100")
        print(f"  Confidence: {result.confidence:.0%}")
        print(f"\n  Breakdown:")
        for dimension, score in result.breakdown.items():
            print(f"    {dimension:20}: {score:5.1f}/100")

        if result.skill_gaps:
            print(f"\n  Missing Skills ({len(result.skill_gaps)}): {', '.join(result.skill_gaps)}")

        print(f"\n  Analysis: {result.explanation}")
        print("-" * 70)

        # Every score is a valid percentage with an explanation
        assert 0.0 <= result.overall_score <= 100.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.explanation

    # The exact-match ML Engineer job should score well above the role
    # this profile is missing core required skills for (TensorFlow/Kubernetes)
    assert results["job-1"].overall_score > results["job-2"].overall_score
    # Job 1 requires only skills the profile already has
    assert results["job-1"].skill_gaps == []
    # Job 2 requires TensorFlow and Kubernetes, neither of which is in the profile
    assert "TensorFlow" in results["job-2"].skill_gaps
    assert "Kubernetes" in results["job-2"].skill_gaps

    print("\nOK: Semantic matcher working\n")


def test_gap_analyzer():
    """Test gap analysis."""
    print("=" * 70)
    print("TEST 2: Gap Analyzer")
    print("=" * 70)

    analyzer = GapAnalyzer()
    profile = create_test_profile()
    jobs = create_test_jobs()

    # Filter to relevant jobs (good matches)
    target_jobs = [jobs[0], jobs[2]]  # Skip senior role

    print(f"\nAnalyzing gaps for {len(target_jobs)} target jobs...")

    gaps = analyzer.analyze(profile, target_jobs)

    print(f"\nFound {len(gaps)} skill gaps:")
    print("-" * 70)

    for i, gap in enumerate(gaps[:5], 1):  # Top 5
        print(f"\n{i}. {gap.skill}")
        print(f"   Current: L{gap.current_level.value} ({gap.current_level.name})")
        print(f"   Target:  L{gap.target_level.value} ({gap.target_level.name})")
        print(f"   Learning Cost: {gap.learning_cost_hours} hours")
        print(f"   Impact Score: {gap.impact_score:.1f}")
        print(f"   ROI: {gap.roi:.2f} (impact per hour)")
        print(f"   Jobs Unlocked: {gap.jobs_unlocked}")

        if gap.learning_path and len(gap.learning_path) > 1:
            print(f"   Path: {' -> '.join(gap.learning_path)}")

    print("\n" + "-" * 70)

    # Neither target job requires anything the profile doesn't already have
    # at INDEPENDENT+, except AWS, PostgreSQL, Kubernetes, Redis
    gap_skills = {g.skill for g in gaps}
    assert gap_skills == {"AWS", "Kubernetes", "PostgreSQL", "Redis"}

    # Gaps must be sorted by ROI descending
    rois = [g.roi for g in gaps]
    assert rois == sorted(rois, reverse=True)

    # Every gap has a positive learning cost. Learning path is only non-empty
    # for skills the profile doesn't already have some level in (shortest_
    # learning_path returns [] for a skill the profile already "knows", even
    # if below the target proficiency level).
    for gap in gaps:
        assert gap.learning_cost_hours > 0
        if gap.current_level == SkillLevel.UNKNOWN:
            assert gap.learning_path

    print("\nOK: Gap analyzer working\n")


def test_learning_roadmap():
    """Test roadmap generation."""
    print("=" * 70)
    print("TEST 3: Learning Roadmap")
    print("=" * 70)

    analyzer = GapAnalyzer()
    profile = create_test_profile()
    jobs = create_test_jobs()

    target_jobs = [jobs[0], jobs[2]]

    gaps = analyzer.analyze(profile, target_jobs)

    # Generate 8-week roadmap, 10 hours/week
    roadmap = analyzer.create_roadmap(gaps, hours_per_week=10, max_weeks=8)

    print(f"\n{roadmap.summary()}")

    print("\n" + "-" * 70)
    print("Detailed Schedule:")
    print("-" * 70)

    for task in roadmap.tasks:
        print(f"\nWeek {task.start_week}-{task.start_week + task.duration_weeks - 1}: {task.skill}")
        print(f"  Time: {task.hours_per_week}h/week x {task.duration_weeks} weeks = {task.total_hours}h total")
        print(f"  Impact: +{task.impact:.1f} career value")
        print(f"  Resources:")
        for resource in task.resources:
            print(f"    - {resource}")
        print(f"  Validation: {task.validation}")

    print("\n" + "-" * 70)
    print(f"\nTotal Investment: {roadmap.total_hours} hours over {roadmap.total_weeks} weeks")
    print(f"Expected ROI: +{roadmap.expected_fit_improvement:.0f}% fit score improvement")

    # The roadmap must respect the requested ceiling
    assert roadmap.total_weeks <= 8
    assert roadmap.tasks
    # Tasks are scheduled back-to-back without overlapping weeks
    for earlier, later in zip(roadmap.tasks, roadmap.tasks[1:]):
        assert later.start_week >= earlier.start_week + earlier.duration_weeks
    # Total hours across tasks matches the sum of individual task hours
    assert roadmap.total_hours == sum(t.total_hours for t in roadmap.tasks)

    print("\nOK: Roadmap generator working\n")


def test_integration(matcher):
    """Test full pipeline."""
    print("=" * 70)
    print("TEST 4: Full Integration")
    print("=" * 70)

    analyzer = GapAnalyzer()

    profile = create_test_profile()
    jobs = create_test_jobs()

    print("\nStep 1: Match jobs")
    print("-" * 70)

    matches = []
    for job in jobs:
        result = matcher.match(profile, job)
        matches.append((job, result))
        print(f"{job.title:30} | Score: {result.overall_score:5.1f} | Gaps: {len(result.skill_gaps)}")

    # Filter good matches
    good_matches = [(j, r) for j, r in matches if r.overall_score >= 60]

    print(f"\n{len(good_matches)} jobs with score >= 60")

    print("\nStep 2: Analyze gaps for good matches")
    print("-" * 70)

    target_jobs = [j for j, r in good_matches]
    gaps = analyzer.analyze(profile, target_jobs) if target_jobs else []

    print(f"\nTop 3 skills to learn (by ROI):")
    for i, gap in enumerate(gaps[:3], 1):
        print(f"  {i}. {gap.skill:15} | ROI: {gap.roi:5.2f} | Cost: {gap.learning_cost_hours:3}h | Jobs: {gap.jobs_unlocked}")

    print("\nStep 3: Generate learning plan")
    print("-" * 70)

    roadmap = analyzer.create_roadmap(gaps, hours_per_week=10, max_weeks=8)

    print(f"\nLearning Plan: {roadmap.total_weeks} weeks")
    for task in roadmap.tasks:
        print(f"  Week {task.start_week:2}: {task.skill} ({task.total_hours}h)")

    print(f"\nExpected Outcome:")
    print(f"  Time investment: {roadmap.total_hours} hours")
    print(f"  Fit improvement: +{roadmap.expected_fit_improvement:.0f}%")

    # The full pipeline must produce internally consistent results: every
    # match has a score, and the roadmap (if any gaps exist) stays within budget
    assert all(0.0 <= r.overall_score <= 100.0 for _, r in matches)
    assert roadmap.total_weeks <= 8

    print("\nOK: Integration working\n")


if __name__ == "__main__":
    m = SemanticMatcher(model_name='all-MiniLM-L6-v2')
    test_semantic_matcher(m)
    test_gap_analyzer()
    test_learning_roadmap()
    test_integration(m)
    print("=" * 70)
    print("  OK: ALL DAY 2 TESTS PASSED")
    print("=" * 70)
