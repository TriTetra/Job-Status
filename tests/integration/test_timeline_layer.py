"""Test Timeline Layer — 5 tests."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

try:
    from dotenv import load_dotenv
    for _env in [Path(".env"), Path("services/hiring-agent/.env")]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass


def test_track_snapshot():
    print("\n[TEST 1] Track snapshot")
    from core.timeline import Timeline

    tl = Timeline()
    snapshot = tl.track_snapshot(
        entity_type="job",
        entity_id="https://example.com/job-123",
        data={"career_score": 78.0, "company": "Google", "title": "ML Engineer"},
    )

    print(f"  Snapshot id: {snapshot.id}")
    assert snapshot.id is not None
    print("  PASS")


def test_detect_changes():
    print("\n[TEST 2] Auto change detection")
    from core.timeline import Timeline

    tl = Timeline()
    entity_id = "https://example.com/job-change-test"

    tl.track_snapshot(
        entity_type="job",
        entity_id=entity_id,
        data={"career_score": 78.0, "company": "Google"},
        snapshot_at=datetime.utcnow() - timedelta(days=2),
    )

    tl.track_snapshot(
        entity_type="job",
        entity_id=entity_id,
        data={"career_score": 91.0, "company": "Google", "salary": 150000},
    )

    changes = tl.detect_changes("job", entity_id, days=7)
    print(f"  Changes detected: {len(changes)}")
    for c in changes:
        print(f"    {c.format_for_display()}")

    assert len(changes) >= 2

    score_change = next((c for c in changes if c.field_name == "career_score"), None)
    assert score_change is not None
    assert float(score_change.old_value) == 78.0
    assert float(score_change.new_value) == 91.0
    print("  PASS")


def test_get_entity_history():
    print("\n[TEST 3] Entity history")
    from core.timeline import Timeline

    tl = Timeline()
    entity_id = "https://example.com/job-history-test"

    for i, days_ago in enumerate([5, 3, 1]):
        tl.track_snapshot(
            entity_type="job",
            entity_id=entity_id,
            data={"career_score": 70.0 + i * 10, "version": i},
            snapshot_at=datetime.utcnow() - timedelta(days=days_ago),
            detect_changes=False,
        )

    history = tl.get_entity_history("job", entity_id, days=7)
    print(f"  History length: {len(history)}")
    for h in history:
        print(f"    {h['snapshot_at'].strftime('%Y-%m-%d')}: score={h['data']['career_score']}")

    assert len(history) >= 3
    assert history[0]["data"]["version"] == 2   # newest first
    print("  PASS")


def test_trending_entities():
    print("\n[TEST 4] Trending entities")
    from core.timeline import Timeline

    tl = Timeline()
    base_ts = datetime.utcnow() - timedelta(days=10)

    entities = [
        ("skill_python", 100, 150),   # +50 %
        ("skill_rust",   50,  80),    # +60 %
        ("skill_php",   100,  70),    # -30 %
        ("skill_go",     80, 120),    # +50 %
    ]

    for eid, old, new in entities:
        tl.track_snapshot("skill", eid, {"job_count": old}, snapshot_at=base_ts)
        tl.track_snapshot("skill", eid, {"job_count": new})

    trending = tl.get_trending_entities("skill", "job_count", days=14, limit=3, direction="up")
    print("  Top trending up:")
    for t in trending:
        print(f"    {t['entity_id']}: {t['old_value']:.0f} -> {t['new_value']:.0f} ({t['change_pct']:+.1f}%)")

    assert len(trending) >= 3
    assert trending[0]["entity_id"] == "skill_rust"
    print("  PASS")


def test_recent_changes_feed():
    print("\n[TEST 5] Recent changes feed")
    from core.timeline import Timeline

    tl = Timeline()

    all_changes = tl.get_recent_changes(days=7, limit=20)
    print(f"  Recent changes (all types): {len(all_changes)}")

    job_changes = tl.get_recent_changes(entity_type="job", days=7, limit=10)
    print(f"  Recent job changes: {len(job_changes)}")

    if all_changes:
        print("  Sample:")
        for c in all_changes[:3]:
            print(f"    [{c.entity_type}] {c.entity_id[:35]}: {c.format_for_display()}")

    # Both test 1 and test 2 created job snapshots this session
    assert len(job_changes) > 0
    print("  PASS")


def main():
    print("=" * 60)
    print("  Timeline Layer Test Suite")
    print("=" * 60)

    tests = [
        test_track_snapshot,
        test_detect_changes,
        test_get_entity_history,
        test_trending_entities,
        test_recent_changes_feed,
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
