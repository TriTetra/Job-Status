"""
Test target-aware resume generator.

Usage:
    python scripts/test_resume_generator.py

Note: Tests 1, 2, 4, 5 make real OpenRouter API calls (~$0.01-0.02 total)
"""

import sys


def test_llm_client():
    print("\n[TEST 1] LLM Client")
    from careeros.shared.llm import get_llm_client

    client = get_llm_client()
    response = client.complete("Say 'CareerOS' and nothing else.", max_tokens=20)
    assert "CareerOS" in response, f"Unexpected response: {response}"
    print(f"  Response: {response.strip()}")
    print("  PASS")


def test_llm_json_mode():
    print("\n[TEST 2] LLM JSON mode")
    from careeros.shared.llm import get_llm_client

    client = get_llm_client()
    result = client.complete_json(
        'Return JSON with keys "test" (value "ok") and "value" (integer 42)', json_mode=True
    )
    assert result.get("test") == "ok"
    assert result.get("value") == 42
    print(f"  Parsed: {result}")
    print("  PASS")


def test_evidence_loading():
    print("\n[TEST 3] Evidence loading (no LLM)")
    from careeros.resume.resume_generator import ResumeGenerator

    gen = ResumeGenerator(user_id="default")
    evidence, projects = gen._load_evidence()

    print(f"  Skills with evidence: {len(evidence)}")
    print(f"  GitHub projects: {len(projects)}")

    if evidence:
        top = sorted(evidence.items(), key=lambda x: x[1]["confidence"], reverse=True)[:3]
        for skill, data in top:
            print(f"  - {skill}: {data['confidence']:.2f} ({len(data['evidence_list'])} projects)")

    assert len(evidence) > 0, "No evidence found — upload a CV or sync GitHub first"
    print("  PASS")


def test_extract_priorities():
    print("\n[TEST 4] Extract priorities (LLM)")
    from careeros.resume.resume_generator import ResumeGenerator

    gen = ResumeGenerator(user_id="default")
    priorities = gen._extract_priorities(
        title="ML Engineer",
        company="Google",
        description="Looking for ML engineer with PyTorch, computer vision, and research experience.",
    )

    print(f"  must_have: {priorities.get('must_have', [])}")
    print(f"  important: {priorities.get('important', [])}")
    print(f"  summary: {priorities.get('summary', '')[:80]}")
    assert "must_have" in priorities
    print("  PASS")


def test_full_generation():
    print("\n[TEST 5] Full resume generation E2E (LLM x4)")
    from careeros.resume.resume_generator import generate_resume

    output = generate_resume(
        target_company="Google",
        target_title="ML Engineer",
        template_name="ml_research",
        job_description="",
        user_id="default",
    )

    assert output.exists(), f"Output file not found: {output}"
    content = output.read_text(encoding="utf-8")

    assert "# " in content, "Missing heading"
    assert "## Summary" in content, "Missing summary"
    assert "Google" in content, "Target company not in resume"
    assert "ML Engineer" in content, "Target title not in resume"

    print(f"  Output: {output}")
    print(f"  Size: {len(content)} chars, {len(content.splitlines())} lines")
    preview = content[:400].encode("ascii", errors="replace").decode("ascii")
    print(f"\n  Preview:\n  {preview[:200]}")
    print("  PASS")


def main():
    print("=" * 60)
    print("  Resume Generator Test Suite")
    print("=" * 60)
    print("  Tests 1, 2, 4, 5 make real OpenRouter API calls (~$0.01-0.02)")
    print("=" * 60)

    tests = [
        test_llm_client,
        test_llm_json_mode,
        test_evidence_loading,
        test_extract_priorities,
        test_full_generation,
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
