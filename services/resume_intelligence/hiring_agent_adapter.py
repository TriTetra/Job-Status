"""
Adapter: hiring-agent (score.py + CSV) → career_scores PostgreSQL table.

Public API:
    score_resume(pdf_path)                   → scores dict (from CSV)
    build_and_enrich(pdf_path, session)      → runs score.py + evidence + enriches DB
    enrich_career_scores(session, scores)    → writes resume_score into explanation JSONB
"""

import csv
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HIRING_AGENT_DIR = Path(__file__).parent.parent / "hiring-agent"  # services/hiring-agent
CSV_PATH = HIRING_AGENT_DIR / "resume_evaluations.csv"

_SCORE_COLS = {
    "open_source_score", "open_source_max",
    "self_projects_score", "self_projects_max",
    "production_score", "production_max",
    "technical_skills_score", "technical_skills_max",
    "total_score", "total_max",
    "bonus_points", "deductions",
    "total_work_experience", "total_education",
    "total_skills", "total_projects",
    "github_repos", "github_followers", "github_following",
}


class HiringAgentAdapter:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path).resolve()
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"CV not found: {self.pdf_path}")

    def run(self) -> dict[str, Any]:
        """Run score.py and return parsed scores from the CSV."""
        _run_score(self.pdf_path)
        return _read_last_csv_row()


def score_resume(pdf_path: str | Path) -> dict[str, Any]:
    """One-liner: run hiring-agent on pdf_path, return scores dict."""
    return HiringAgentAdapter(pdf_path).run()


def build_and_enrich(pdf_path: str | Path, session) -> dict[str, Any]:
    """
    Full pipeline:
      1. Run score.py → CSV
      2. Build Evidence Graph from GitHub cache + CSV
      3. Enrich career_scores.explanation with resume_score + skill confidences

    Returns the scores dict.
    """
    scores = score_resume(pdf_path)

    # Extract basename for cache lookup (e.g. "Abdullokh_Abdukodirov.pdf" → "Abdullokh_Abdukodirov")
    basename = Path(pdf_path).stem

    print("\nBuilding Evidence Graph...")
    from services.resume_intelligence.application.evidence_builder import build_evidence_graph
    confidences = build_evidence_graph(basename)

    print("\nEnriching career_scores...")
    enriched = _build_enrichment_payload(scores)
    enriched["skill_confidence"] = confidences
    n = _enrich_db(session, enriched)
    print(f"Updated {n} career_score rows")

    return scores


def enrich_career_scores(session, resume_scores: dict[str, Any]) -> int:
    """
    Merge resume_scores into career_scores.explanation for rows not yet enriched.
    Returns number of rows updated.
    """
    enrichment = _build_enrichment_payload(resume_scores)
    if not enrichment:
        return 0
    return _enrich_db(session, enrichment)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _run_score(pdf_path: Path) -> None:
    venv_python = HIRING_AGENT_DIR / ".venv" / "Scripts" / "python.exe"
    python = str(venv_python) if venv_python.exists() else sys.executable

    result = subprocess.run(
        [python, "score.py", str(pdf_path)],
        cwd=str(HIRING_AGENT_DIR),
        capture_output=False,
        text=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        raise RuntimeError(f"score.py exited with code {result.returncode}")


def _read_last_csv_row() -> dict[str, Any]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("resume_evaluations.csv is empty")

    return _cast_row(rows[-1])


def _cast_row(raw: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if k in _SCORE_COLS:
            try:
                out[k] = float(v)
            except (ValueError, TypeError):
                out[k] = None
        else:
            out[k] = v or None
    return out


def _build_enrichment_payload(scores: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "open_source_score", "open_source_max",
        "self_projects_score", "self_projects_max",
        "production_score", "production_max",
        "technical_skills_score", "technical_skills_max",
        "total_score", "total_max",
        "bonus_points", "bonus_breakdown",
        "deductions", "deduction_reasons",
        "key_strengths", "areas_for_improvement",
        "github_repos", "github_followers",
    ]
    return {k: scores[k] for k in keys if k in scores}


def _enrich_db(session, enrichment: dict[str, Any]) -> int:
    from sqlalchemy import select
    from packages.db.models.career_score import CareerScore

    stmt = select(CareerScore).where(
        CareerScore.explanation["resume_score"].is_(None)
    )
    rows = session.execute(stmt).scalars().all()
    for row in rows:
        merged = dict(row.explanation)
        merged["resume_score"] = enrichment
        row.explanation = merged

    session.flush()
    return len(rows)
