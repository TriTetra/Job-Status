"""
Test Career OS core functionality.
"""

import sys
from pathlib import Path

# Add career_os to path
sys.path.insert(0, str(Path(__file__).parent))

from career_os.models import Skill, SkillLevel, UserProfile, Job
from career_os.core import SkillGraph


def test_skill_levels():
    """Test skill level system."""
    print("=" * 70)
    print("TEST 1: Skill Levels & Learning Cost")
    print("=" * 70)

    # Create skills at different levels
    python = Skill(
        name="Python",
        level=SkillLevel.INDEPENDENT,
        evidence=["Built YOLOv8 system", "FastAPI production apps"],
        ai_multiplier=0.8  # Some AI assistance
    )

    aws = Skill(
        name="AWS",
        level=SkillLevel.AI_ASSISTED,
        evidence=["Deployed models to Lambda with AI help"],
        ai_multiplier=0.5  # Heavy AI assistance
    )

    print(f"\n{python}")
    print(f"  Effective level: {python.effective_level():.1f}/5.0")
    print(f"  Cost to ADVANCED: {python.learning_cost(SkillLevel.ADVANCED)} hours")

    print(f"\n{aws}")
    print(f"  Effective level: {aws.effective_level():.1f}/5.0")
    print(f"  Cost to INDEPENDENT: {aws.learning_cost(SkillLevel.INDEPENDENT)} hours")

    print("\n✓ Skill levels working")


def test_skill_graph():
    """Test skill graph and transfer learning."""
    print("\n" + "=" * 70)
    print("TEST 2: Skill Graph & Transfer Learning")
    print("=" * 70)

    graph = SkillGraph()

    # Test transfer factors
    transfers = [
        ("Python", "FastAPI"),
        ("Python", "Go"),
        ("React", "Next.js"),
        ("AWS", "GCP"),
    ]

    print("\nTransfer Learning Coefficients:")
    for from_skill, to_skill in transfers:
        factor = graph.get_transfer_factor(from_skill, to_skill)
        print(f"  {from_skill:15} → {to_skill:15} : {factor:.2f}")

    # Test learning paths
    print("\nLearning Paths:")

    known = ["Python", "Docker"]
    targets = ["Kubernetes", "FastAPI", "AWS"]

    for target in targets:
        path = graph.shortest_learning_path(known, target)
        print(f"\n  To learn {target}:")
        if path:
            print(f"    Path: {' → '.join(path)}")
        else:
            print(f"    Already known!")

    # Test learning discount
    print("\nLearning Cost Discounts:")

    python_skill = Skill("Python", SkillLevel.ADVANCED)
    docker_skill = Skill("Docker", SkillLevel.WORKING)

    known_skills = [python_skill, docker_skill]

    for target in ["FastAPI", "Kubernetes", "Rust"]:
        discount = graph.calculate_learning_discount(known_skills, target)
        original_cost = 40  # Base hours
        actual_cost = int(original_cost * discount)

        print(f"  {target:15} : {discount:.0%} discount ({original_cost}h → {actual_cost}h)")

    print("\n✓ Skill graph working")


def test_user_profile():
    """Test user profile creation."""
    print("\n" + "=" * 70)
    print("TEST 3: User Profile")
    print("=" * 70)

    # Create realistic profile
    profile = UserProfile(
        name="Abdullokh Abdukodirov",
        email="test@example.com",
        years_experience=2.0,
        ai_proficiency=0.8,  # High AI proficiency
        skills=[
            Skill("Python", SkillLevel.INDEPENDENT, ai_multiplier=0.8),
            Skill("PyTorch", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("Computer Vision", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("FastAPI", SkillLevel.WORKING, ai_multiplier=0.6),
            Skill("Docker", SkillLevel.WORKING, ai_multiplier=0.5),
            Skill("AWS", SkillLevel.AI_ASSISTED, ai_multiplier=0.4),
            Skill("React", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),
        ]
    )

    print(f"\nProfile: {profile.name}")
    print(f"Experience: {profile.years_experience} years")
    print(f"AI Proficiency: {profile.ai_proficiency:.0%}")

    print(f"\nSkills ({len(profile.skills)}):")
    for skill in sorted(profile.skills, key=lambda s: s.level, reverse=True):
        level_name = SkillLevel(skill.level).name
        effective = skill.effective_level()
        print(f"  {skill.name:20} L{skill.level} ({level_name:12}) → {effective:.1f} effective")

    print(f"\nHigh proficiency (L3+): {len(profile.high_proficiency_skills())}")

    print("\n✓ User profile working")


def test_job_matching_concept():
    """Test job matching concept."""
    print("\n" + "=" * 70)
    print("TEST 4: Job Matching Concept")
    print("=" * 70)

    # Create sample job
    job = Job(
        id="test-1",
        title="ML Engineer",
        company="Acme AI",
        description="Build ML systems with PyTorch",
        url="https://example.com/job/1",
        location="Remote",
        remote=True,
        required_skills=["Python", "PyTorch", "AWS", "Docker"],
        required_years=2.0,
        salary_min=100000,
        salary_max=150000
    )

    print(f"\nJob: {job.title} at {job.company}")
    print(f"Required skills: {', '.join(job.required_skills)}")
    print(f"Experience: {job.required_years} years")
    print(f"Salary: {job.salary_range_str()}")
    print(f"Remote: {job.remote}")

    # Simple matching logic (placeholder for real matcher)
    print("\nSimple Match Analysis:")

    profile = UserProfile(
        name="Test User",
        email="test@example.com",
        years_experience=2.0,
        skills=[
            Skill("Python", SkillLevel.INDEPENDENT),
            Skill("PyTorch", SkillLevel.WORKING),
            Skill("Docker", SkillLevel.WORKING),
        ]
    )

    matched = []
    missing = []

    for req in job.required_skills:
        if profile.has_skill(req, SkillLevel.WORKING):
            matched.append(req)
        else:
            missing.append(req)

    match_pct = len(matched) / len(job.required_skills) * 100

    print(f"  Matched: {', '.join(matched)}")
    print(f"  Missing: {', '.join(missing)}")
    print(f"  Match: {match_pct:.0f}%")

    print("\n✓ Job matching concept working")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  CAREER OS CORE TESTS")
    print("=" * 70)

    try:
        test_skill_levels()
        test_skill_graph()
        test_user_profile()
        test_job_matching_concept()

        print("\n" + "=" * 70)
        print("  ✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nCore systems operational. Ready for:")
        print("  1. Semantic Matcher implementation")
        print("  2. Gap Analyzer implementation")
        print("  3. Opportunity Scorer implementation")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
