"""
Test ApplyPilot job source plugin.

Usage:
    python scripts/test_applypilot_plugin.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from plugins.plugin_loader import list_available_job_sources, load_job_source_plugin


def test_list_sources():
    print("\n[TEST 1] List available job sources")
    sources = list_available_job_sources()
    assert "applypilot" in sources
    assert sources["applypilot"]["enabled"] is True
    for name, info in sources.items():
        status = "OK" if info["enabled"] else "--"
        print(f"  [{status}] {name} v{info['version']} -- {info['description']}")
    print(f"  PASS -- {len(sources)} source(s)")


def test_load_plugin():
    print("\n[TEST 2] Load ApplyPilot plugin")
    plugin = load_job_source_plugin("applypilot")
    meta = plugin.get_metadata()
    assert meta["name"] == "applypilot"
    assert meta["enabled"] is True
    assert meta["job_count"] >= 0
    print(f"  name: {meta['name']}  version: {meta['version']}")
    print(f"  db_path: {meta['db_path']}")
    print(f"  job_count: {meta['job_count']}")
    print("  PASS")


def test_scan():
    print("\n[TEST 3] Scan raw jobs")
    plugin = load_job_source_plugin("applypilot")
    jobs = plugin.scan(hours_old=1500, min_score=7)
    assert len(jobs) > 0, "No jobs found -- try hours_old=720 or check DB"
    assert "url" in jobs[0]
    assert "title" in jobs[0]
    print(f"  Found {len(jobs)} jobs")
    print(f"  Sample: {jobs[0].get('title','?')[:60]}")
    print("  PASS")


def test_normalize():
    print("\n[TEST 4] Normalize single job")
    plugin = load_job_source_plugin("applypilot")
    raw_jobs = plugin.scan(hours_old=1500, min_score=7)
    assert raw_jobs

    job = plugin.normalize(raw_jobs[0])

    required = [
        "url", "title", "company", "description", "location",
        "remote", "required_skills", "required_years", "company_size", "source",
    ]
    for f in required:
        assert f in job, f"Missing field: {f}"

    print(f"  title:    {job['title'][:50]}")
    print(f"  company:  {job['company']}")
    print(f"  location: {job['location']}")
    print(f"  remote:   {job['remote']}")
    skills_preview = ", ".join(job["required_skills"][:4]) or "(none)"
    print(f"  skills:   {len(job['required_skills'])} -- {skills_preview}")
    print(f"  years:    {job['required_years']}")
    print(f"  size:     {job['company_size']}")
    print(f"  fit:      {job['fit_score']}")
    print("  PASS")


def test_scan_and_normalize():
    print("\n[TEST 5] scan_and_normalize (convenience)")
    plugin = load_job_source_plugin("applypilot")
    jobs = plugin.scan_and_normalize(hours_old=1500, min_score=8)
    assert len(jobs) > 0
    assert all("url" in j for j in jobs)
    companies = {j["company"] for j in jobs}
    print(f"  Jobs: {len(jobs)}   Unique companies: {len(companies)}")
    for j in jobs[:3]:
        score = f"{j['fit_score']:.0f}" if j["fit_score"] else "?"
        print(f"  [{score}] {j['title'][:40]} @ {j['company']}")
    print("  PASS")


def test_company_extraction():
    print("\n[TEST 6] Company extraction rate")
    plugin = load_job_source_plugin("applypilot")
    raw_jobs = plugin.scan(hours_old=1500, min_score=7)
    sample = raw_jobs[:min(50, len(raw_jobs))]

    known = sum(1 for r in sample if plugin.normalize(r)["company"] != "Unknown")
    pct = known / len(sample) * 100 if sample else 0

    print(f"  Known: {known}/{len(sample)} ({pct:.1f}%)")
    print(f"  Unknown: {len(sample) - known}/{len(sample)}")
    assert pct >= 30, f"Extraction rate too low: {pct:.1f}%"
    print("  PASS")


def main():
    print("=" * 60)
    print("  ApplyPilot Plugin Test Suite")
    print("=" * 60)

    tests = [
        test_list_sources,
        test_load_plugin,
        test_scan,
        test_normalize,
        test_scan_and_normalize,
        test_company_extraction,
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
