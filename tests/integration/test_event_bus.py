"""Test event bus implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from core.events import event_bus
from core.events.job_events import JobDiscovered, JobScored
from core.events.application_events import ApplicationSubmitted
from core.events.resume_events import ResumeGenerated


def test_basic_pubsub():
    print("\n[TEST 1] Basic pub/sub")
    event_bus.clear()
    received = []

    event_bus.subscribe(JobScored, lambda e: received.append(e))
    event_bus.publish(JobScored(job_id="https://example.com/job1", title="ML Engineer", company="Google", career_score=87.5, recommendation="APPLY"))

    assert len(received) == 1
    assert received[0].career_score == 87.5
    print(f"  OK -- received {len(received)} event, score={received[0].career_score}")


def test_multiple_subscribers():
    print("\n[TEST 2] Multiple subscribers")
    event_bus.clear()
    counts = {"a": 0, "b": 0}

    event_bus.subscribe(JobScored, lambda e: counts.__setitem__("a", counts["a"] + 1))
    event_bus.subscribe(JobScored, lambda e: counts.__setitem__("b", counts["b"] + 1))
    event_bus.publish(JobScored(job_id="x", career_score=75))

    assert counts["a"] == 1 and counts["b"] == 1
    print(f"  OK -- both handlers invoked: {counts}")


def test_type_isolation():
    print("\n[TEST 3] Type isolation")
    event_bus.clear()
    job_recv = []
    app_recv = []

    event_bus.subscribe(JobScored, lambda e: job_recv.append(e))
    event_bus.subscribe(ApplicationSubmitted, lambda e: app_recv.append(e))

    event_bus.publish(JobScored(job_id="job1", career_score=80))
    event_bus.publish(ApplicationSubmitted(job_id="job2", company="Stripe"))

    assert len(job_recv) == 1 and len(app_recv) == 1
    assert job_recv[0].job_id == "job1"
    assert app_recv[0].company == "Stripe"
    print(f"  OK -- JobScored: {len(job_recv)}, ApplicationSubmitted: {len(app_recv)}")


def test_error_isolation():
    print("\n[TEST 4] Error isolation")
    event_bus.clear()
    success = [0]

    def failing(e):
        raise ValueError("Intentional failure")

    def ok(e):
        success[0] += 1

    event_bus.subscribe(JobScored, failing)
    event_bus.subscribe(JobScored, ok)

    result = event_bus.publish(JobScored(job_id="x"))

    assert result == 1
    assert success[0] == 1
    print(f"  OK -- error contained, success_handlers={result}")


def test_history():
    print("\n[TEST 5] Event history")
    event_bus.clear()

    for i in range(5):
        event_bus.publish(JobScored(job_id=f"job{i}", career_score=70 + i))
        event_bus.publish(JobDiscovered(job_id=f"disc{i}", title=f"Job {i}"))

    all_hist = event_bus.get_history()
    scored_hist = event_bus.get_history(JobScored)

    assert len(all_hist) == 10
    assert len(scored_hist) == 5
    print(f"  OK -- total={len(all_hist)}, JobScored only={len(scored_hist)}")


def test_decorator_syntax():
    print("\n[TEST 6] Decorator syntax")
    event_bus.clear()
    received = []

    @event_bus.subscribe(ResumeGenerated)
    def on_resume(event):
        received.append(event)

    event_bus.publish(ResumeGenerated(user_id="aao0", resume_version="google_ml_v3", target_company="Google"))

    assert len(received) == 1
    assert received[0].target_company == "Google"
    print(f"  OK -- decorator works, company={received[0].target_company}")


def test_stats():
    print("\n[TEST 7] Bus statistics")
    event_bus.clear()

    event_bus.subscribe(JobScored, lambda e: None)
    event_bus.subscribe(JobDiscovered, lambda e: None)

    event_bus.publish(JobScored(job_id="x"))
    event_bus.publish(JobScored(job_id="y"))
    event_bus.publish(JobDiscovered(job_id="z"))

    s = event_bus.stats()
    assert s["subscriber_count"] == 2
    assert s["event_types"] == 2
    assert s["publish_count"] == 3
    print(f"  OK -- stats: {s}")


def test_unsubscribe():
    print("\n[TEST 8] Unsubscribe")
    event_bus.clear()
    received = []

    def handler(e):
        received.append(e)

    event_bus.subscribe(JobScored, handler)
    event_bus.publish(JobScored(job_id="x"))
    assert len(received) == 1

    event_bus.unsubscribe(JobScored, handler)
    event_bus.publish(JobScored(job_id="y"))
    assert len(received) == 1  # still 1 — handler removed

    print(f"  OK -- handler removed, received stays at {len(received)}")


def main():
    print("=" * 60)
    print("  Event Bus Test Suite")
    print("=" * 60)

    tests = [
        test_basic_pubsub,
        test_multiple_subscribers,
        test_type_isolation,
        test_error_isolation,
        test_history,
        test_decorator_syntax,
        test_stats,
        test_unsubscribe,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAILED: {e}")

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
