"""
Test domain migration (Week 3).

Usage:
    python scripts/test_domain_migration.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_new_imports():
    print("\n[TEST 1] New imports (packages.domain.*)")
    from packages.domain import (
        Skill, SkillLevel,
        UserProfile, UserPreferences, Experience,
        Job,
        MatchResult, OpportunityScore,
    )
    skill = Skill("Python", SkillLevel.INDEPENDENT)
    assert skill.name == "Python"
    assert skill.level == SkillLevel.INDEPENDENT
    assert skill.effective_level() == 3.0

    job = Job(id="j1", title="Engineer", company="Acme",
              description="Build stuff", url="https://acme.com")
    assert job.all_skills() == []

    profile = UserProfile(name="Test", email="t@t.com", years_experience=3.0)
    assert profile.has_skill("Python") is False
    profile.update_skill("Python", SkillLevel.INDEPENDENT)
    assert profile.has_skill("Python")

    print("  PASS")


def test_sub_package_imports():
    print("\n[TEST 2] Sub-package imports")
    from packages.domain.identity import Skill, SkillLevel, UserProfile, UserPreferences, Experience
    from packages.domain.job import Job
    from packages.domain.intelligence import MatchResult, OpportunityScore

    j = Job(id="x", title="x", company="x", description="x", url="x")
    m = MatchResult(job=j, overall_score=75.0, breakdown={}, skill_gaps=[], confidence=0.8)
    assert "75.0" in m.summary()

    o = OpportunityScore(job=j, fit_score=80, acceptance_probability=0.5,
                         career_value=70, market_demand=85, career_score=78, expected_value=40)
    assert o.priority_tier() == "MEDIUM"
    assert o.should_apply(threshold=70.0) is True
    print("  PASS")


def test_shim_imports():
    print("\n[TEST 3] Backward-compat shims (career_os.models.*)")
    from career_os.models import (
        Skill, SkillLevel, SKILL_CATEGORIES, categorize_skill,
        UserProfile, UserPreferences, Experience,
        Job, MatchResult, OpportunityScore,
    )
    skill = Skill("Go", SkillLevel.WORKING)
    assert skill.name == "Go"
    cats = SKILL_CATEGORIES
    assert "languages" in cats
    assert categorize_skill("Python") == "languages"
    assert categorize_skill("nonexistent") is None
    print("  PASS")


def test_class_identity():
    print("\n[TEST 4] Shim re-exports same classes (no copies)")
    from packages.domain import Skill as DomainSkill, Job as DomainJob
    from career_os.models import Skill as ShimSkill, Job as ShimJob

    assert DomainSkill is ShimSkill, "Skill class mismatch"
    assert DomainJob is ShimJob, "Job class mismatch"
    print("  PASS -- DomainSkill is ShimSkill, DomainJob is ShimJob")


def test_intelligence_modules_import():
    print("\n[TEST 5] packages/intelligence/*.py import with new paths")
    from packages.intelligence import SemanticMatcher, OpportunityScorer, GapAnalyzer
    assert SemanticMatcher is not None
    assert OpportunityScorer is not None
    assert GapAnalyzer is not None
    print("  PASS")


def test_applypilot_loader():
    print("\n[TEST 6] career_os.data.applypilot_loader imports")
    from career_os.data.applypilot_loader import ApplyPilotLoader, create_user_profile_from_config
    assert ApplyPilotLoader is not None
    assert create_user_profile_from_config is not None
    print("  PASS")


def test_skill_graph():
    print("\n[TEST 7] career_os.core.skill_graph imports")
    from career_os.core.skill_graph import SkillGraph
    assert SkillGraph is not None
    print("  PASS")


def main():
    print("=" * 60)
    print("  Domain Migration Test Suite (Week 3)")
    print("=" * 60)

    tests = [
        test_new_imports,
        test_sub_package_imports,
        test_shim_imports,
        test_class_identity,
        test_intelligence_modules_import,
        test_applypilot_loader,
        test_skill_graph,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
