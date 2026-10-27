"""
Test prompts template loader.

Usage:
    python scripts/test_prompts.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))


def test_template_loader():
    print("\n[TEST 1] Template Loader")
    from core.prompts import template_loader

    templates = template_loader.list_templates()
    assert len(templates) >= 4, f"Expected >=4 templates, got {len(templates)}"

    jinja_templates = [t for t in templates if t.endswith(".jinja")]
    print(f"  Available templates ({len(jinja_templates)}):")
    for t in jinja_templates:
        print(f"    - {t}")
    print("  PASS")


def test_tailor_prompt():
    print("\n[TEST 2] tailor_for_target.jinja")
    from core.prompts import template_loader

    output = template_loader.render(
        "resume/tailor_for_target.jinja",
        target_company="Google",
        target_title="ML Engineer",
        required_skills=["Python", "PyTorch", "Computer Vision"],
        preferred_skills=["Docker", "Kubernetes"],
        job_description=None,
        evidence={
            "Computer Vision": {
                "confidence": 0.85,
                "evidence_list": [
                    {
                        "project_name": "Project-Drone-Vision",
                        "author_commits": 142,
                        "stars": 38,
                        "github_url": "https://github.com/TriTetra/Project-Drone-Vision",
                    }
                ],
            },
            "Python": {
                "confidence": 0.92,
                "evidence_list": [
                    {
                        "project_name": "evolutionary-tsp",
                        "author_commits": 47,
                        "stars": 2,
                        "github_url": "https://github.com/TriTetra/evolutionary-tsp",
                    }
                ],
            },
        },
        projects=[],
    )

    assert "Google" in output
    assert "ML Engineer" in output
    assert "Project-Drone-Vision" in output
    assert "Evidence > Claim" in output
    print(f"  Output length: {len(output)} chars")
    print(f"  Preview: {output[:120].strip()}...")
    print("  PASS")


def test_summary_prompt():
    print("\n[TEST 3] generate_summary.jinja")
    from core.prompts import template_loader

    output = template_loader.render(
        "resume/generate_summary.jinja",
        target_company="Google",
        target_title="ML Engineer",
        candidate_name="Abdullokh Abdukodirov",
        years_experience=2,
        education="Bachelor's in Computer Engineering",
        top_skills={
            "Computer Vision": 0.85,
            "Python": 0.92,
            "PyTorch": 0.78,
        },
        featured_projects=[
            {"name": "IMMUNO-TCR", "highlight": "92% mAP on edge devices"},
            {"name": "Project-Drone-Vision", "highlight": "YOLOv8 + synthetic data"},
        ],
    )

    assert "Google" in output
    assert "ML Engineer" in output
    assert "92% mAP" in output
    print(f"  Output length: {len(output)} chars")
    print("  PASS")


def test_project_selection_prompt():
    print("\n[TEST 4] select_projects.jinja")
    from core.prompts import template_loader

    output = template_loader.render(
        "resume/select_projects.jinja",
        target_company="Stripe",
        target_title="Backend Engineer",
        max_projects=3,
        projects=[
            {
                "name": "evolutionary-tsp",
                "author_commit_count": 47,
                "github_details": {
                    "stars": 2,
                    "language": "Python",
                    "topics": ["algorithm", "streamlit"],
                    "description": "High-performance Evolutionary TSP Solver",
                    "size": 1200,
                },
            },
            {
                "name": "Project-Drone-Vision",
                "author_commit_count": 142,
                "github_details": {
                    "stars": 38,
                    "language": "Jupyter Notebook",
                    "topics": ["yolov8", "opencv", "computer-vision"],
                    "description": "End-to-end CV pipeline",
                    "size": 5000,
                },
            },
        ],
    )

    assert "Stripe" in output
    assert "Backend Engineer" in output
    assert "evolutionary-tsp" in output
    print(f"  Output length: {len(output)} chars")
    print("  PASS")


def test_job_priorities_prompt():
    print("\n[TEST 5] extract_priorities.jinja")
    from core.prompts import template_loader

    output = template_loader.render(
        "job/extract_priorities.jinja",
        job_title="ML Engineer",
        job_company="Google",
        job_description="""
We are looking for an ML Engineer with strong Python and PyTorch experience.
Must have: Computer Vision, deep learning, production deployment.
Nice to have: Kubernetes, TensorFlow, research publications.
3+ years of experience required.
        """,
    )

    assert "ML Engineer" in output
    assert "Google" in output
    assert "must_have" in output
    print(f"  Output length: {len(output)} chars")
    print("  PASS")


def main():
    print("=" * 60)
    print("  Prompts Jinja Test Suite")
    print("=" * 60)

    tests = [
        test_template_loader,
        test_tailor_prompt,
        test_summary_prompt,
        test_project_selection_prompt,
        test_job_priorities_prompt,
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
