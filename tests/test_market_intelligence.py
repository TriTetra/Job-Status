"""Test Market Intelligence — 6 tests. Makes real API calls."""

import sys
from datetime import datetime
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


def _find_thread(client):
    """Find the most recent Who is Hiring thread (current or previous month)."""
    now = datetime.utcnow()
    thread = client.find_who_is_hiring_thread(now.year, now.month)
    if not thread:
        prev_month = now.month - 1 or 12
        prev_year = now.year if now.month > 1 else now.year - 1
        thread = client.find_who_is_hiring_thread(prev_year, prev_month)
    return thread


def test_hn_client():
    print("\n[TEST 1] HN Algolia Client")
    from plugins.market_signals.hackernews.client import HackerNewsClient

    client = HackerNewsClient()
    thread = _find_thread(client)

    assert thread is not None, "No Who is Hiring thread found"
    print(f"  Thread: {thread.get('title')}")
    print(f"  ID: {thread.get('objectID')}")

    comments = client.get_top_level_comments(int(thread["objectID"]))
    print(f"  Comments: {len(comments)}")
    assert len(comments) > 50, f"Expected 50+ comments, got {len(comments)}"
    print("  PASS")


def test_who_is_hiring_parser():
    print("\n[TEST 2] Who is Hiring Parser")
    from plugins.market_signals.hackernews.client import HackerNewsClient
    from plugins.market_signals.hackernews.who_is_hiring_parser import WhoIsHiringParser

    client = HackerNewsClient()
    parser = WhoIsHiringParser()

    thread = _find_thread(client)
    comments = client.get_top_level_comments(int(thread["objectID"]))
    assert comments, "No comments"

    parsed_any = False
    for c in comments[:10]:
        job = parser.parse_comment(c)
        if job.get("company"):
            print(f"  Company: {job['company']}")
            print(f"  Role:    {job['role']}")
            print(f"  Remote:  {job['remote']}")
            print(f"  Skills:  {job['skills'][:4]}")
            parsed_any = True
            break

    assert parsed_any, "No comment could be parsed"
    print("  PASS")


def test_hn_signal_extraction():
    print("\n[TEST 3] HN Signal Extraction (DB write)")
    from plugins.market_signals.hackernews.signal_extractor import HNSignalExtractor
    from core.db.connection import db
    from core.db.repositories import MarketSignalRepository

    now = datetime.utcnow()
    extractor = HNSignalExtractor()
    count = extractor.extract_monthly_signals(now.year, now.month)

    if count == 0:
        prev_month = now.month - 1 or 12
        prev_year = now.year if now.month > 1 else now.year - 1
        count = extractor.extract_monthly_signals(prev_year, prev_month)

    print(f"  Signals created/deduped: {count}")

    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        recent = repo.get_recent(days=60, limit=5)
        print(f"  DB records (60d): {len(recent)}")
        if recent:
            print(f"  Latest: {recent[0].title[:60]}")

    assert count >= 0
    print("  PASS")


def test_techcrunch_extraction():
    print("\n[TEST 4] TechCrunch Extraction")
    from plugins.market_signals.techcrunch.signal_extractor import TechCrunchSignalExtractor

    extractor = TechCrunchSignalExtractor()
    count = extractor.extract_signals(hours=168)
    print(f"  Signals created: {count}")
    # 0 is acceptable if no funding/layoff news this week
    print("  PASS")


def test_skill_trend():
    print("\n[TEST 5] Skill Trend")
    from core.db.connection import db
    from core.db.repositories import MarketSignalRepository

    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        trend = repo.get_skill_trend("Python", days=60)

    print(f"  Python ({60}d): current={trend['current_count']}, "
          f"change={trend['change_percent']:+.1f}%, dir={trend['direction']}")
    assert trend["current_count"] >= 0
    print("  PASS")


def test_market_summary():
    print("\n[TEST 6] Market Summary")
    from core.db.connection import db
    from core.db.repositories import MarketSignalRepository

    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        s = repo.get_market_summary(days=60)

    total = sum(s["signal_counts"].values())
    print(f"  Total signals (60d): {total}")
    print(f"  Top skills: {[x['skill'] for x in s['top_skills'][:5]]}")
    print(f"  Top companies: {[x['company'] for x in s['top_companies'][:5]]}")
    assert total > 0, "Expected some signals after HN extraction"
    print("  PASS")


def main():
    print("=" * 60)
    print("  Market Intelligence Test Suite")
    print("=" * 60)
    print("  Makes real API calls: HN Algolia, TechCrunch RSS")
    print("=" * 60)

    tests = [
        test_hn_client,
        test_who_is_hiring_parser,
        test_hn_signal_extraction,
        test_techcrunch_extraction,
        test_skill_trend,
        test_market_summary,
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
