"""
Test multi-user migration.

Usage:
    python scripts/test_multiuser_migration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import func, select, text

from packages.db.connection import db
from packages.db.repositories import (
    CareerScoreRepository,
    ApplicationRepository,
    EvidenceRepository,
    ScanHistoryRepository,
)


def test_user_id_columns_exist():
    print("\n[TEST 1] user_id columns exist in all tables")
    tables = ["career_scores", "applications", "emails", "scan_history", "evidence"]
    with db.session_scope() as s:
        for tbl in tables:
            row = s.execute(text(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = '{tbl}' AND column_name = 'user_id'
            """)).fetchone()
            assert row is not None, f"user_id missing from {tbl}"
            count = s.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            print(f"  {tbl:<20} OK  ({count} rows)")
    print("  PASS")


def test_existing_data_backfilled():
    print("\n[TEST 2] Existing rows have user_id='default'")
    tables_with_repos = [
        ("career_scores", CareerScoreRepository),
        ("scan_history", ScanHistoryRepository),
        ("evidence", EvidenceRepository),
    ]
    with db.session_scope() as s:
        for tbl, RepoClass in tables_with_repos:
            repo = RepoClass(s)
            total = s.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            default_count = s.execute(text(
                f"SELECT COUNT(*) FROM {tbl} WHERE user_id = 'default'"
            )).scalar()
            assert default_count == total, f"{tbl}: {default_count}/{total} have user_id='default'"
            print(f"  {tbl:<20} {default_count}/{total} rows = 'default'")
    print("  PASS")


def test_user_isolation():
    print("\n[TEST 3] User isolation — career_scores")
    test_url = "https://example.com/test-isolation-job"
    user_a = "test_user_a"
    user_b = "test_user_b"

    with db.session_scope() as s:
        repo = CareerScoreRepository(s)
        repo.save_score(user_id=user_a, url=test_url, career_score=80.0, fit_score=85.0,
                        acceptance_probability=70.0, career_value=75.0, market_demand=80.0,
                        expected_value=45.0, recommendation="APPLY")
        repo.save_score(user_id=user_b, url=test_url, career_score=90.0, fit_score=95.0,
                        acceptance_probability=80.0, career_value=85.0, market_demand=90.0,
                        expected_value=60.0, recommendation="APPLY")

    with db.session_scope() as s:
        repo = CareerScoreRepository(s)
        score_a = repo.get_latest_score(url=test_url, user_id=user_a)
        score_b = repo.get_latest_score(url=test_url, user_id=user_b)

        assert score_a is not None and score_a.career_score == 80.0, f"user_a score wrong: {score_a}"
        assert score_b is not None and score_b.career_score == 90.0, f"user_b score wrong: {score_b}"
        print(f"  user_a career_score = {score_a.career_score}")
        print(f"  user_b career_score = {score_b.career_score}")

        # Cleanup
        s.execute(text(f"DELETE FROM career_scores WHERE url = '{test_url}'"))

    print("  PASS")


def test_config_user_id():
    print("\n[TEST 4] config.yaml has user.id")
    from career_os.config_loader import load_config
    cfg = load_config()
    assert "user" in cfg, "config.yaml missing 'user' section"
    assert "id" in cfg["user"], "config.yaml missing 'user.id'"
    print(f"  user.id = '{cfg['user']['id']}'")
    print(f"  user.name = '{cfg['user'].get('name', '?')}'")
    print("  PASS")


def test_scan_history_user_isolation():
    print("\n[TEST 5] ScanHistoryRepository.get_all_known_urls filters by user_id")
    test_url = "https://example.com/test-scan-history"
    with db.session_scope() as s:
        repo = ScanHistoryRepository(s)
        repo.record_scan(user_id="u1", url=test_url, applypilot_score=8,
                         career_os_score=None, discovered_in_this_scan=True)
        urls_u1 = repo.get_all_known_urls(user_id="u1")
        urls_u2 = repo.get_all_known_urls(user_id="u2")
        assert test_url in urls_u1, "u1 should see their URL"
        assert test_url not in urls_u2, "u2 should NOT see u1's URL"
        print(f"  u1 sees {test_url[:40]}... YES")
        print(f"  u2 sees it: NO")
        s.execute(text(f"DELETE FROM scan_history WHERE url = '{test_url}'"))
    print("  PASS")


def main():
    print("=" * 60)
    print("  Multi-User Migration Test Suite")
    print("=" * 60)

    tests = [
        test_user_id_columns_exist,
        test_existing_data_backfilled,
        test_user_isolation,
        test_config_user_id,
        test_scan_history_user_isolation,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed += 1
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
