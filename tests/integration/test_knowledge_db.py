"""Test Knowledge DB — 6 tests (DB-First)."""

import sys


from careeros.shared.config import load_env

load_env()


def test_seed():
    print("\n[TEST 1] Seed from YAML")
    from scripts.seed_knowledge_from_yaml import seed_countries, seed_salaries, seed_visas

    countries = seed_countries()
    visas = seed_visas()
    salaries = seed_salaries()

    assert countries == 5, f"Expected 5 countries, got {countries}"
    assert visas == 3, f"Expected 3 visas, got {visas}"
    assert salaries >= 20, f"Expected 20+ salary ranges, got {salaries}"

    print(f"  PASS ({countries} countries, {visas} visas, {salaries} salaries)")


def test_country_queries():
    print("\n[TEST 2] Country repository")
    from careeros.db.connection import db
    from careeros.knowledge.repositories.country_repo import CountryRepository

    with db.session_scope() as session:
        repo = CountryRepository(session)

        germany = repo.get_by_iso("DE")
        assert germany is not None, "Germany not found"
        assert germany.name == "Germany"
        assert germany.currency == "EUR"
        print(f"  Germany: {germany.name} ({germany.currency})")
        print(f"  Tech hubs: {len(germany.tech_hubs)}")
        assert len(germany.tech_hubs) >= 2

        results = repo.search_by_name("United")
        assert any(c.iso_code == "US" for c in results), "USA not in search results"
        print(f"  Search 'United': {len(results)} results")

        all_c = repo.get_all()
        assert len(all_c) >= 5
        print(f"  Total countries: {len(all_c)}")

    print("  PASS")


def test_visa_queries():
    print("\n[TEST 3] Visa repository")
    from careeros.db.connection import db
    from careeros.knowledge.repositories.visa_repo import VisaRepository

    with db.session_scope() as session:
        repo = VisaRepository(session)

        blue_card = repo.get_by_type("EU Blue Card")
        assert blue_card is not None, "EU Blue Card not found"
        assert blue_card.description is not None
        print(f"  EU Blue Card: {blue_card.description[:60]}...")

        de_visas = repo.get_for_country("DE")
        assert len(de_visas) >= 1
        print(f"  DE visas: {[v.visa_type for v in de_visas]}")

        all_v = repo.get_all()
        assert len(all_v) >= 3
        print(f"  Total visas: {len(all_v)}")

    print("  PASS")


def test_salary_queries():
    print("\n[TEST 4] Salary repository")
    from careeros.db.connection import db
    from careeros.knowledge.repositories.salary_repo import SalaryRangeRepository

    with db.session_scope() as session:
        repo = SalaryRangeRepository(session)

        roles = repo.get_all_roles()
        print(f"  Roles: {roles}")
        assert len(roles) >= 2

        ml = repo.get_salary("ML Engineer")
        print(f"  ML Engineer records: {len(ml)}")
        assert len(ml) > 0

        for s in ml[:3]:
            print(f"    {s.country or s.region}: {s.level} = "
                  f"{s.min_salary:,}-{s.max_salary:,} {s.currency}")

        summary = repo.get_role_summary("ML Engineer")
        print(f"  Summary: {summary['total_records']} records, "
              f"{summary['regions']} regions")

    print("  PASS")


def test_update_salary():
    print("\n[TEST 5] Update salary (UI simulation)")
    from careeros.db.connection import db
    from careeros.knowledge.repositories.salary_repo import SalaryRangeRepository

    with db.session_scope() as session:
        repo = SalaryRangeRepository(session)
        salaries = repo.get_salary("ML Engineer")
        if not salaries:
            print("  No ML salaries — skip")
            return

        s = salaries[0]
        orig_id, orig_min, orig_max = s.id, s.min_salary, s.max_salary
        print(f"  Original: {orig_min:,}-{orig_max:,}")

        updated = repo.update_salary(orig_id, orig_min + 5000, orig_max + 10000, "test_ui")
        print(f"  Updated: {updated.min_salary:,}-{updated.max_salary:,}")
        assert updated.last_updated_by == "test_ui"
        assert updated.median_salary == (updated.min_salary + updated.max_salary) // 2

        repo.update_salary(orig_id, orig_min, orig_max, "test_revert")
        print("  Reverted")

    print("  PASS")


def test_no_yaml_at_runtime():
    print("\n[TEST 6] No runtime YAML dependency")
    from careeros.db.connection import db
    from careeros.knowledge.repositories.country_repo import CountryRepository
    from careeros.knowledge.repositories.salary_repo import SalaryRangeRepository
    from careeros.knowledge.repositories.visa_repo import VisaRepository

    with db.session_scope() as session:
        countries = CountryRepository(session).get_all()
        visas = VisaRepository(session).get_all()
        roles = SalaryRangeRepository(session).get_all_roles()

    print(f"  DB-only: {len(countries)} countries, {len(visas)} visas, {len(roles)} roles")
    assert len(countries) >= 5
    assert len(visas) >= 3
    assert len(roles) >= 2
    print("  PASS")


def main():
    print("=" * 60)
    print("  Knowledge DB Test Suite (DB-First)")
    print("=" * 60)

    tests = [
        test_seed,
        test_country_queries,
        test_visa_queries,
        test_salary_queries,
        test_update_salary,
        test_no_yaml_at_runtime,
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
