"""
Test user_settings and user_custom_skills tables + per-user scorer weights.

Usage:
    python scripts/test_user_settings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from sqlalchemy import inspect
from core.db.connection import db


def test_table_exists():
    print("\n[TEST 1] user_settings and user_custom_skills tables exist")
    with db.session_scope() as s:
        tables = inspect(s.connection()).get_table_names()
    assert "user_settings" in tables, "user_settings missing — run alembic upgrade head"
    assert "user_custom_skills" in tables, "user_custom_skills missing — run alembic upgrade head"
    print("  PASS")


def test_default_user_seeded():
    print("\n[TEST 2] 'default' user seeded in user_settings")
    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        row = repo.get_settings("default")
        assert row is not None, "default user not found — migration may not have run"
        assert "fit" in row.weights
        assert abs(row.weights["fit"] - 0.30) < 0.001
        weights_snapshot = dict(row.weights)
    print("  PASS — default weights:", weights_snapshot)


def test_upsert_and_weights():
    print("\n[TEST 3] Upsert user settings and read back custom weights")
    test_user = "test_weights_user"

    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        repo.upsert(
            test_user,
            profile={"name": "Test User", "years_experience": 3},
            skills=[{"name": "Python", "level": "INDEPENDENT", "ai_multiplier": 0.8}],
            preferences={"remote": True, "work_visa_required": False},
            weights={"fit": 0.50, "acceptance": 0.20, "career_value": 0.20, "market_demand": 0.10},
        )

    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        weights = repo.get_weights(test_user)
        assert abs(weights["fit"] - 0.50) < 0.001, f"fit weight mismatch: {weights}"
        assert abs(weights["market_demand"] - 0.10) < 0.001

        # Cleanup
        row = repo.get_settings(test_user)
        s.delete(row)

    print("  PASS")


def test_custom_skills():
    print("\n[TEST 4] Custom skills round-trip")
    test_user = "test_custom_skills_user"

    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        repo.add_custom_skill(test_user, "Blender", "3d")
        repo.add_custom_skill(test_user, "Figma", "design")

    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        names = repo.get_custom_skills(test_user)
        assert "Blender" in names
        assert "Figma" in names
        repo.remove_custom_skill(test_user, "Blender")

    with db.session_scope() as s:
        from core.db.repositories import UserSettingsRepository
        repo = UserSettingsRepository(s)
        names2 = repo.get_custom_skills(test_user)
        assert "Blender" not in names2
        assert "Figma" in names2
        repo.remove_custom_skill(test_user, "Figma")

    print("  PASS")


def test_scorer_weights():
    print("\n[TEST 5] OpportunityScorer respects per-user weights")
    from core.intelligence import OpportunityScorer
    from core.domain import Job, UserProfile, Skill, SkillLevel

    scorer = OpportunityScorer()
    job = Job(
        id="j1",
        title="ML Engineer",
        company="Acme",
        description="Python, PyTorch",
        url="https://acme.com/j1",
        required_skills=["Python", "PyTorch"],
        remote=True,
        required_years=2.0,
        company_size="startup",
    )
    user = UserProfile(
        name="Test",
        email="t@t.com",
        years_experience=3.0,
        skills=[Skill("Python", SkillLevel.INDEPENDENT), Skill("PyTorch", SkillLevel.WORKING)],
    )

    score_default = scorer.score(job, user)
    score_fit_only = scorer.score(
        job, user,
        weights={"fit": 1.0, "acceptance": 0.0, "career_value": 0.0, "market_demand": 0.0},
    )

    assert abs(score_default.career_score - score_fit_only.career_score) > 0.5, (
        f"Weights had no effect: default={score_default.career_score:.1f} "
        f"fit_only={score_fit_only.career_score:.1f}"
    )
    print(f"  PASS — default={score_default.career_score:.1f}, fit_only={score_fit_only.career_score:.1f}")


def main():
    print("=" * 60)
    print("  User Settings Test Suite")
    print("=" * 60)

    tests = [
        test_table_exists,
        test_default_user_seeded,
        test_upsert_and_weights,
        test_custom_skills,
        test_scorer_weights,
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
