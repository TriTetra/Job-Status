"""
Test GitHub Enrichment pipeline.

Usage:
    python scripts/test_github_enrichment.py

Makes real GitHub API calls. Needs GITHUB_TOKEN in environment.
"""

import sys
from pathlib import Path


# Load .env so GITHUB_TOKEN / OPENROUTER_API_KEY are available
try:
    from dotenv import load_dotenv
    _root = Path(__file__).parents[2]
    for _env in [_root / ".env", _root / "services" / "hiring-agent" / ".env"]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass


def test_github_client():
    print("\n[TEST 1] GitHub Client + rate limit")
    from plugins.enrichment.github.client import GitHubClient

    client = GitHubClient()
    rate = client.check_rate_limit()
    print(f"  Rate limit: {rate['remaining']}/{rate['limit']} — reset {rate['reset']}")
    assert rate["remaining"] > 0, "GitHub rate limit exhausted"
    print("  PASS")


def test_repo_analyzer():
    print("\n[TEST 2] Repo Analyzer on TriTetra/Project-Drone-Vision")
    from plugins.enrichment.github.client import GitHubClient
    from plugins.enrichment.github.repo_analyzer import RepoAnalyzer

    client = GitHubClient()
    analyzer = RepoAnalyzer()

    repo = client.get_repo("TriTetra/Project-Drone-Vision")
    metrics = analyzer.analyze(repo)

    print(f"  LOC:        {metrics['loc_count']:,}")
    print(f"  Language:   {metrics['language']}")
    print(f"  Topics:     {metrics['topics']}")
    print(f"  PRs:        {metrics['pr_count']}")
    print(f"  Issues:     {metrics['issue_count']}")
    print(f"  has_tests:  {metrics['has_tests']}")
    print(f"  has_docs:   {metrics['has_docs']}")
    print(f"  commit/wk:  {metrics['commit_frequency']:.2f}")

    assert metrics["loc_count"] > 0, "Expected LOC > 0"
    assert metrics["language"] is not None, "Expected primary language"
    print("  PASS")


def test_enrichment_pipeline():
    print("\n[TEST 3] Full enrichment pipeline")
    from plugins.enrichment.github.evidence_enricher import EvidenceEnricher
    from core.db.connection import db
    from core.db.repositories import EvidenceRepository

    enricher = EvidenceEnricher(user_id="default")
    enriched = enricher.enrich_all_projects()
    print(f"  Enriched {enriched} projects")

    with db.session_scope() as session:
        repo = EvidenceRepository(session)
        all_ev = repo.get_all_evidence_for_user("default")
        with_loc = [ev for ev in all_ev if ev.loc_count is not None]

        print(f"  Records with LOC: {len(with_loc)}/{len(all_ev)}")
        for ev in sorted(with_loc, key=lambda e: e.loc_count or 0, reverse=True)[:3]:
            print(f"    {ev.project_name}: {ev.loc_count:,} LOC, {ev.language}, conf={ev.confidence:.2f}")

        assert len(with_loc) > 0, "No records were enriched"
    print("  PASS")


def test_confidence_improved():
    print("\n[TEST 4] Confidence scores improved after enrichment")
    from core.db.connection import db
    from core.db.repositories import EvidenceRepository

    with db.session_scope() as session:
        repo = EvidenceRepository(session)
        summary = repo.skill_summary("default")

        print("  Top 5 skills by confidence:")
        top5 = sorted(summary.items(), key=lambda x: x[1]["avg_confidence"], reverse=True)[:5]
        for skill, stats in top5:
            bar = "#" * int(stats["avg_confidence"] * 20)
            print(f"    {skill:<22} {stats['avg_confidence']:.2f}  {bar}")

        max_conf = max(s["avg_confidence"] for s in summary.values()) if summary else 0
        assert max_conf > 0.40, f"Expected max confidence > 0.40, got {max_conf:.2f}"

    print("  PASS")


def test_real_metrics_in_db():
    print("\n[TEST 5] Real metrics present in DB")
    from core.db.connection import db
    from core.db.repositories import EvidenceRepository

    with db.session_scope() as session:
        repo = EvidenceRepository(session)
        all_ev = repo.get_all_evidence_for_user("default")

        has_loc = sum(1 for ev in all_ev if ev.loc_count)
        has_topics = sum(1 for ev in all_ev if ev.topics)
        has_lang = sum(1 for ev in all_ev if ev.language)

        print(f"  Records with loc_count: {has_loc}/{len(all_ev)}")
        print(f"  Records with topics:    {has_topics}/{len(all_ev)}")
        print(f"  Records with language:  {has_lang}/{len(all_ev)}")

        assert has_loc > 0, "No LOC data stored"
        assert has_lang > 0, "No language data stored"
    print("  PASS")


def main():
    print("=" * 60)
    print("  GitHub Enrichment Test Suite")
    print("=" * 60)
    print("  Makes real GitHub API calls — needs GITHUB_TOKEN")
    print("=" * 60)

    tests = [
        test_github_client,
        test_repo_analyzer,
        test_enrichment_pipeline,
        test_confidence_improved,
        test_real_metrics_in_db,
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
