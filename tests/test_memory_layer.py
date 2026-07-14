"""Test Memory Layer — 6 tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    for _env in [Path(".env"), Path("services/hiring-agent/.env")]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass


def test_candidate_memory():
    print("\n[TEST 1] CandidateMemory")
    from core.memory import CandidateMemory

    memory = CandidateMemory(user_id="test_user")
    memory.clear()

    memory.add_fact(
        fact_type="preference",
        content="User prefers backend roles",
        confidence=0.9,
        source="manual",
    )

    memory.learn_from_application_outcome(
        company="Google",
        stage="phone_screen",
        outcome="rejected",
        job_title="ML Engineer",
    )

    facts = memory.get_facts()
    print(f"  Facts added: {len(facts)}")
    assert len(facts) == 2, f"Expected 2, got {len(facts)}"

    matched = memory.search("backend")
    print(f"  Search 'backend': {len(matched)} matches")
    assert len(matched) == 1

    print("  PASS")


def test_candidate_memory_application_analysis():
    print("\n[TEST 2] CandidateMemory — remote vs onsite analysis")
    from core.memory import CandidateMemory

    memory = CandidateMemory(user_id="test_user")
    result = memory.analyze_remote_vs_onsite()

    print(f"  Remote apps: {result['remote_application_count']}")
    print(f"  Onsite apps: {result['onsite_application_count']}")
    print(f"  Recommendation: {result['recommendation']}")
    assert result["recommendation"] in ("prefer_remote", "prefer_onsite", "neutral")
    print("  PASS")


def test_company_memory():
    print("\n[TEST 3] CompanyMemory")
    from core.memory import CompanyMemory

    memory = CompanyMemory(user_id="test_memory_user")

    memory.add_fact(
        fact_type="interview_topic",
        content="Google asked Docker and Redis",
        confidence=1.0,
        metadata={"company_name": "Google", "topics": ["Docker", "Redis"]},
        source="interview_notes",
    )

    facts = memory.get_facts_for_company("Google")
    print(f"  Facts for Google: {len(facts)}")
    assert len(facts) >= 1

    summary = memory.get_summary()
    assert isinstance(summary, str)
    print("  PASS")


def test_market_memory():
    print("\n[TEST 4] MarketMemory")
    from core.memory import MarketMemory

    memory = MarketMemory(user_id="test_user")

    facts = memory.get_facts(limit=10)
    print(f"  Market signals (30d): {len(facts)}")

    trend = memory.get_skill_trend("Python", days=30)
    print(f"  Python trend: {trend['direction']} ({trend['change_percent']:+.1f}%)")
    assert trend["current_count"] >= 0

    top = memory.get_top_skills(days=7, limit=5)
    print(f"  Top skills: {[s['skill'] for s in top]}")

    print("  PASS")


def test_conversation_memory():
    print("\n[TEST 5] ConversationMemory")
    from core.memory import ConversationMemory

    memory = ConversationMemory(user_id="test_user")

    memory.add_fact(
        fact_type="user_query",
        content="User asked about Google ML Engineer role",
        source="conversation",
    )
    memory.add_fact(
        fact_type="user_preference",
        content="User prefers concise explanations",
        source="conversation",
    )

    context = memory.get_context_for_prompt(max_facts=5)
    print(f"  Context length: {len(context)} chars")
    assert "Google" in context

    memory.clear()
    assert len(memory.get_facts()) == 0
    print("  PASS")


def test_learning_memory():
    print("\n[TEST 6] LearningMemory")
    from core.memory import LearningMemory

    memory = LearningMemory(user_id="test_user")

    memory.add_fact(
        fact_type="optimal_hours",
        content="User learns best with 12 hours/week",
        confidence=0.8,
        metadata={"hours": 12},
        source="manual",
    )

    plan = memory.get_optimal_study_plan()
    print(f"  Optimal hours: {plan['hours_per_week']}")
    print(f"  Format: {plan['preferred_format']}")
    assert plan["hours_per_week"] == 12
    print("  PASS")


def main():
    print("=" * 60)
    print("  Memory Layer Test Suite")
    print("=" * 60)

    tests = [
        test_candidate_memory,
        test_candidate_memory_application_analysis,
        test_company_memory,
        test_market_memory,
        test_conversation_memory,
        test_learning_memory,
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
