"""
Test Feature Registry.

Usage:
    python scripts/test_feature_registry.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_registry_loads_features():
    print("\n[TEST 1] Feature discovery")
    from features import feature_registry

    features = feature_registry.list_features()
    print(f"  Discovered features ({len(features)}):")
    for name in features:
        meta = feature_registry.get_feature(name)
        flag = "ON " if meta.get("enabled") else "OFF"
        rollout = meta.get("rollout_percentage", 0)
        print(f"    [{flag}] {name} v{meta.get('version')} (rollout: {rollout}%)")

    assert "resume_ai" in features
    assert "target_aware_resume" in features
    assert "feedback_learning" in features
    print("  PASS")


def test_is_enabled_basic():
    print("\n[TEST 2] is_enabled -- basic cases")
    from features import feature_registry

    assert feature_registry.is_enabled("resume_ai") is True
    assert feature_registry.is_enabled("target_aware_resume") is True
    assert feature_registry.is_enabled("feedback_learning") is False
    assert feature_registry.is_enabled("nonexistent_feature") is False

    print("  resume_ai: enabled")
    print("  target_aware_resume: enabled")
    print("  feedback_learning: disabled (expected)")
    print("  nonexistent_feature: False (safe default)")
    print("  PASS")


def test_deterministic_rollout():
    print("\n[TEST 3] Deterministic rollout")
    from features import feature_registry

    user_ids = [f"user_{i}" for i in range(20)]

    buckets_1 = [feature_registry.get_rollout_bucket("resume_ai", uid) for uid in user_ids]
    buckets_2 = [feature_registry.get_rollout_bucket("resume_ai", uid) for uid in user_ids]

    assert buckets_1 == buckets_2, "Rollout must be deterministic"
    assert all(0 <= b < 100 for b in buckets_1)

    unique_buckets = len(set(buckets_1))
    assert unique_buckets >= 10, f"Too few unique buckets: {unique_buckets}"

    print(f"  20 users -> {unique_buckets} unique buckets")
    print(f"  Sample buckets: {buckets_1[:5]}")
    print("  PASS")


def test_get_enabled_features():
    print("\n[TEST 4] get_enabled_features")
    from features import feature_registry

    enabled = feature_registry.get_enabled_features(user_id="abdullokh")
    print(f"  Enabled for 'abdullokh': {enabled}")

    assert "resume_ai" in enabled
    assert "target_aware_resume" in enabled
    assert "feedback_learning" not in enabled
    print("  PASS")


def test_dependencies():
    print("\n[TEST 5] Dependency checking")
    from features import feature_registry

    deps = feature_registry.check_dependencies("target_aware_resume")
    print(f"  target_aware_resume deps: {deps}")
    assert "resume_ai" in deps
    assert deps["resume_ai"] is True

    deps2 = feature_registry.check_dependencies("feedback_learning")
    print(f"  feedback_learning deps: {deps2}")
    assert "resume_ai" in deps2
    assert "target_aware_resume" in deps2
    print("  PASS")


def test_feature_metadata():
    print("\n[TEST 6] Feature metadata")
    from features import feature_registry

    meta = feature_registry.get_feature("target_aware_resume")
    assert meta is not None
    assert meta["name"] == "target_aware_resume"
    assert meta["version"] == "1.0.0"
    assert "description" in meta
    assert "metrics" in meta
    assert "requires" in meta

    print(f"  name: {meta['name']}")
    print(f"  version: {meta['version']}")
    print(f"  description: {meta['description']}")
    print(f"  metrics: {meta['metrics']}")
    print(f"  requires: {meta['requires']}")
    print("  PASS")


def main():
    print("=" * 60)
    print("  Feature Registry Test Suite")
    print("=" * 60)

    tests = [
        test_registry_loads_features,
        test_is_enabled_basic,
        test_deterministic_rollout,
        test_get_enabled_features,
        test_dependencies,
        test_feature_metadata,
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
