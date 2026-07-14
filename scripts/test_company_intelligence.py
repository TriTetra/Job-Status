"""Test Company Intelligence — 6 tests."""

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


def test_knowledge_loader():
    print("\n[TEST 1] Knowledge loader")
    from packages.knowledge import CompanyLoader

    loader = CompanyLoader()
    all_companies = loader.load_all()

    print(f"  Loaded {len(all_companies)} companies")
    assert "google" in all_companies, "google not found"
    assert "stripe" in all_companies, "stripe not found"
    assert all_companies["google"]["tier"] == "big_tech"
    assert all_companies["stripe"]["tier"] == "unicorn"
    assert "Python" in all_companies["google"]["tech_stack"]

    print(f"  big_tech: {list(loader.get_by_tier('big_tech').keys())}")
    print(f"  unicorn:  {list(loader.get_by_tier('unicorn').keys())}")
    print("  PASS")


def test_seed_from_knowledge():
    print("\n[TEST 2] Seed Company table from knowledge YAML")
    from services.company_intelligence.application.company_enricher import CompanyEnricher
    from packages.db.connection import db
    from packages.db.repositories import CompanyRepository

    count = CompanyEnricher().seed_from_knowledge()
    print(f"  Seeded {count} companies")

    with db.session_scope() as session:
        repo = CompanyRepository(session)
        google = repo.get(name="google")

        assert google is not None, "google not in DB"
        assert google.tier == "big_tech"
        assert "Python" in google.tech_stack
        assert "Go" in google.tech_stack
        assert len(google.interview_rounds) >= 3

        stripe = repo.get(name="stripe")
        assert stripe is not None
        assert "Rust" in stripe.tech_stack

        print(f"  google: tier={google.tier}, {len(google.tech_stack)} tech, {len(google.interview_rounds)} rounds")
        print(f"  stripe: {stripe.tech_stack}")

    print("  PASS")


def test_enrich_from_jobs():
    print("\n[TEST 3] Enrich from job postings")
    from services.company_intelligence.application.company_enricher import CompanyEnricher
    from packages.db.connection import db
    from packages.db.repositories import CompanyRepository

    fake_jobs = [
        {"company": "Stripe", "required_skills": ["Rust", "Go"], "preferred_skills": ["Kafka"]},
        {"company": "Stripe", "required_skills": ["Python", "AWS"], "preferred_skills": []},
        {"company": "BrandNewCo", "required_skills": ["React", "TypeScript"], "preferred_skills": []},
    ]

    processed = CompanyEnricher().enrich_from_job_postings(fake_jobs)
    print(f"  Processed: {processed}")

    with db.session_scope() as session:
        repo = CompanyRepository(session)
        stripe = repo.get(name="Stripe")

        assert stripe is not None
        assert "Rust" in stripe.tech_stack
        assert "Kafka" in stripe.tech_stack
        assert stripe.open_positions_count == 2

        print(f"  Stripe tech after enrichment: {stripe.tech_stack}")

    print("  PASS")


def test_company_memory():
    print("\n[TEST 4] Company memory — record + retrieve")
    from services.company_intelligence.application.company_memory import CompanyMemoryService

    service = CompanyMemoryService(user_id="test_user_3a")

    service.record_application_outcome(
        company_name="google",
        stage="phone_screen",
        outcome="rejected",
        job_title="ML Engineer",
        reason="experience_gap",
    )
    service.record_interview_topics(
        company_name="google",
        topics=["Docker", "Redis", "system_design"],
        round_name="phone_screen",
    )

    advice = service.get_advice_for_company("google")
    print(f"  Summary:        {advice['summary']}")
    print(f"  Recommendation: {advice['recommendation']}")

    assert advice["summary"]["rejection_count"] >= 1
    assert "rejected" in advice["recommendation"].lower()

    topics = service.get_topics_to_study("google")
    assert "Docker" in topics
    print(f"  Topics to study: {topics}")

    print("  PASS")


def test_hiring_now_query():
    print("\n[TEST 5] Hiring now query")
    from packages.db.connection import db
    from packages.db.repositories import CompanyRepository

    with db.session_scope() as session:
        repo = CompanyRepository(session)

        stripe = repo.get(name="stripe")
        if stripe:
            stripe.hiring_trend = "spike"
            stripe.open_positions_count = 15

        google = repo.get(name="google")
        if google:
            google.hiring_trend = "up"
            google.open_positions_count = 50

        session.flush()  # make changes visible to subsequent SELECT in same session

        hiring = repo.get_hiring_now(limit=5)
        names = [c.name for c in hiring]
        print(f"  Hiring now: {names}")
        assert len(hiring) > 0

    print("  PASS")


def test_tech_stack_search():
    print("\n[TEST 6] Tech stack JSONB search")
    from packages.db.connection import db
    from packages.db.repositories import CompanyRepository

    with db.session_scope() as session:
        repo = CompanyRepository(session)
        rust_companies = repo.find_by_tech_stack(["Rust"])
        names = [c.name for c in rust_companies]
        print(f"  Companies with Rust: {names}")
        assert len(names) > 0, "Expected at least one Rust company"

    print("  PASS")


def main():
    print("=" * 60)
    print("  Company Intelligence Test Suite")
    print("=" * 60)

    tests = [
        test_knowledge_loader,
        test_seed_from_knowledge,
        test_enrich_from_jobs,
        test_company_memory,
        test_hiring_now_query,
        test_tech_stack_search,
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
