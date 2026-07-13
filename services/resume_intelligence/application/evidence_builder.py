"""
Evidence Builder — transforms hiring-agent output into Evidence Graph rows.

Input:
  services/hiring-agent/cache/githubcache_<name>.json  (projects + GitHub data)
  services/hiring-agent/resume_evaluations.csv          (LLM scores)

Output:
  evidence table rows: skill × project → confidence
  Dict[skill_name, aggregate_confidence] returned to caller
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

# Allow running directly: python -m services.resume_intelligence.application.evidence_builder
_ROOT = Path(__file__).parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

HIRING_AGENT_DIR = Path(__file__).parents[2] / "hiring-agent"

# GitHub topic → canonical skill name
_TOPIC_MAP: Dict[str, str] = {
    "python": "Python",
    "jupyter": "Python",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "opencv": "OpenCV",
    "yolov8": "YOLOv8",
    "computer-vision": "Computer Vision",
    "deep-learning": "Deep Learning",
    "machine-learning": "Machine Learning",
    "stable-diffusion": "Stable Diffusion",
    "image-processing": "OpenCV",
    "genetic-algorithms": "Algorithms",
    "evolutionary-computing": "Algorithms",
    "optimization": "Algorithms",
    "streamlit": "Streamlit",
    "numpy": "NumPy",
    "data-engineering": "Data Engineering",
    "visualization": "Data Visualization",
    "rust": "Rust",
    "go": "Go",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "fastapi": "FastAPI",
}

# Repo language → canonical skill
_LANG_MAP: Dict[str, str] = {
    "python": "Python",
    "jupyter notebook": "Python",
    "rust": "Rust",
    "go": "Go",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "java": "Java",
}


class EvidenceBuilder:
    def __init__(self, hiring_agent_path: Path = HIRING_AGENT_DIR):
        self.path = hiring_agent_path
        self.csv_path = hiring_agent_path / "resume_evaluations.csv"
        self.cache_dir = hiring_agent_path / "cache"

    def build(self, resume_basename: str = "Abdullokh_Abdukodirov") -> Dict[str, float]:
        """
        Full pipeline: read CSV + cache → write evidence rows → return confidences.

        Returns:
            {skill_name: aggregate_confidence (0.0–1.0)}
        """
        eval_scores = self._read_eval_scores(resume_basename)
        github_data = self._read_github_cache(resume_basename)

        records = self._extract_records(eval_scores, github_data)
        confidences = self._write_to_db(records, eval_scores)

        return confidences

    # ------------------------------------------------------------------
    # Readers
    # ------------------------------------------------------------------

    def _read_eval_scores(self, basename: str) -> dict:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        with self.csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in reversed(rows):
            if basename in row.get("file_name", ""):
                return {
                    "open_source": self._f(row, "open_source_score"),
                    "self_projects": self._f(row, "self_projects_score"),
                    "production": self._f(row, "production_score"),
                    "technical_skills": self._f(row, "technical_skills_score"),
                    "total": self._f(row, "total_score"),
                    "total_max": self._f(row, "total_max"),
                }

        raise ValueError(f"No CSV row found for basename '{basename}'")

    def _read_github_cache(self, basename: str) -> dict:
        cache_file = self.cache_dir / f"githubcache_{basename}.json"
        if not cache_file.exists():
            return {"projects": [], "profile": {}}
        return json.loads(cache_file.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------

    def _extract_records(self, eval_scores: dict, github_data: dict) -> List[dict]:
        records = []
        projects = github_data.get("projects", [])

        for project in projects:
            name = project.get("name", "Unknown")
            url = project.get("github_url")
            commits = project.get("author_commit_count", 0) or 0
            details = project.get("github_details", {})
            stars = details.get("stars", 0) or 0
            topics = details.get("topics", []) or []
            language = (details.get("language") or "").lower()

            skills = self._skills_from_project(topics, language)
            if not skills:
                continue

            for skill in skills:
                confidence = self._confidence(commits, stars, eval_scores)
                records.append(
                    {
                        "skill_name": skill,
                        "project_name": name,
                        "github_url": url,
                        "author_commits": commits,
                        "stars": stars,
                        "confidence": confidence,
                        "evaluation_scores": eval_scores,
                        "evidence_type": "github_project",
                    }
                )

        return records

    def _skills_from_project(self, topics: List[str], language: str) -> List[str]:
        skills = set()

        for topic in topics:
            mapped = _TOPIC_MAP.get(topic.lower())
            if mapped:
                skills.add(mapped)

        if language in _LANG_MAP:
            skills.add(_LANG_MAP[language])

        return list(skills)

    def _confidence(self, commits: int, stars: int, eval_scores: dict) -> float:
        """
        Confidence formula:
          base            = technical_skills / 100          (0.0–1.0)
          commit bonus    = min(commits / 100, 0.20)
          star bonus      = min(stars / 50,   0.10)
          production bonus= (production / 100) * 0.20
        Capped at 1.0.
        """
        base = eval_scores["technical_skills"] / 100
        commit_bonus = min(commits / 100, 0.20)
        star_bonus = min(stars / 50, 0.10)
        prod_bonus = (eval_scores["production"] / 100) * 0.20
        return min(base + commit_bonus + star_bonus + prod_bonus, 1.0)

    # ------------------------------------------------------------------
    # DB write
    # ------------------------------------------------------------------

    def _write_to_db(self, records: List[dict], eval_scores: dict) -> Dict[str, float]:
        from packages.db.connection import db
        from packages.db.repositories import EvidenceRepository

        with db.session_scope() as session:
            repo = EvidenceRepository(session)
            for rec in records:
                repo.add_evidence(**rec)

            # Compute aggregate confidence per skill inside the same session
            skills_seen = {r["skill_name"] for r in records}
            confidences = {
                skill: repo.calculate_skill_confidence(skill)
                for skill in skills_seen
            }

        print(f"Wrote {len(records)} evidence rows ({len(skills_seen)} skills)")
        return confidences

    # ------------------------------------------------------------------

    @staticmethod
    def _f(row: dict, key: str) -> float:
        try:
            return float(row.get(key, 0) or 0)
        except (ValueError, TypeError):
            return 0.0


def build_evidence_graph(
    resume_basename: str = "Abdullokh_Abdukodirov",
) -> Dict[str, float]:
    """Entry point — build evidence graph and return skill confidences."""
    builder = EvidenceBuilder()
    confidences = builder.build(resume_basename)

    print("\nSkill Confidence Scores:")
    print("-" * 44)
    for skill, conf in sorted(confidences.items(), key=lambda x: -x[1]):
        bar = "#" * int(conf * 20)
        print(f"  {skill:<24} {conf:.2f}  {bar}")

    return confidences


if __name__ == "__main__":
    import sys

    basename = sys.argv[1] if len(sys.argv) > 1 else "Abdullokh_Abdukodirov"
    build_evidence_graph(basename)
