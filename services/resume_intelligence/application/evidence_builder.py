"""
Evidence Builder — transforms resume parser output into Evidence Graph rows.

Generic and plugin-based: accepts any ResumeParserPlugin implementation.
Skill mappings come from knowledge/v1/skills/skill_graph.yaml via SkillLoader.
Confidence weights come from config/plugins.yaml.
Nothing is hardcoded here.
"""

import sys
from pathlib import Path
from typing import Dict, List

_ROOT = Path(__file__).parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.config import load_plugin_config
from core.db.connection import db
from core.db.repositories import EvidenceRepository
from core.knowledge import SkillLoader
from plugins.plugin_interface import ResumeData, ResumeParserPlugin


class EvidenceBuilder:
    """Builds Evidence Graph rows from a ResumeParserPlugin output."""

    def __init__(self, parser: ResumeParserPlugin) -> None:
        self.parser = parser
        self._loader = SkillLoader()
        plugin_name = parser.get_metadata()["name"]
        self._conf_cfg = load_plugin_config()["resume_parsers"][plugin_name][
            "confidence_formula"
        ]

    def build(self, pdf_path: Path, basename: str, user_id: str = "default") -> Dict[str, float]:
        """
        Full pipeline: parse -> extract evidence -> write to DB.

        Returns:
            {skill_name: aggregate_confidence (0.0-1.0)}
        """
        resume_data = self.parser.parse(pdf_path, basename)
        records = self._extract_records(resume_data)
        return self._write_to_db(records, user_id=user_id)

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------

    def _extract_records(self, resume_data: ResumeData) -> List[dict]:
        topic_map = self._loader.topic_map
        lang_map = self._loader.language_map
        records: List[dict] = []

        for project in resume_data.projects:
            name = project.get("name", "Unknown")
            url = project.get("github_url")
            commits = project.get("author_commit_count", 0) or 0
            details = project.get("github_details", {})
            stars = details.get("stars", 0) or 0
            topics = [t.lower() for t in (details.get("topics") or [])]
            language = (details.get("language") or "").lower()

            skills: set = set()
            for t in topics:
                if t in topic_map:
                    skills.add(topic_map[t])
            if language in lang_map:
                skills.add(lang_map[language])

            if not skills:
                continue

            conf = self._confidence(commits, stars, resume_data)
            eval_snapshot = {
                "open_source": resume_data.open_source,
                "self_projects": resume_data.self_projects,
                "production": resume_data.production,
                "technical_skills": resume_data.technical_skills,
            }

            for skill in skills:
                records.append(
                    {
                        "skill_name": skill,
                        "project_name": name,
                        "github_url": url,
                        "author_commits": commits,
                        "stars": stars,
                        "confidence": conf,
                        "evaluation_scores": eval_snapshot,
                        "evidence_type": "github_project",
                    }
                )

        return records

    def _confidence(self, commits: int, stars: int, rd: ResumeData) -> float:
        c = self._conf_cfg
        base = rd.technical_skills / c["base_divisor"]
        commit_bonus = min(commits / c["commit_divisor"], c["commit_bonus_max"])
        star_bonus = min(stars / c["star_divisor"], c["star_bonus_max"])
        prod_bonus = (rd.production / 100) * c["production_weight"]
        return min(base + commit_bonus + star_bonus + prod_bonus, 1.0)

    # ------------------------------------------------------------------
    # DB write
    # ------------------------------------------------------------------

    def _write_to_db(self, records: List[dict], user_id: str = "default") -> Dict[str, float]:
        with db.session_scope() as session:
            repo = EvidenceRepository(session)
            for rec in records:
                repo.add_evidence(user_id=user_id, **rec)
            skills_seen = {r["skill_name"] for r in records}
            confidences = {
                skill: repo.calculate_skill_confidence(skill, user_id=user_id)
                for skill in skills_seen
            }
        print(f"Wrote {len(records)} evidence rows ({len(skills_seen)} skills)")
        return confidences


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_evidence_graph(
    pdf_path: Path,
    basename: str,
    parser_name: str = "hiring-agent",
) -> Dict[str, float]:
    """
    Build evidence graph using the specified parser plugin.

    Args:
        pdf_path: Path to resume PDF.
        basename: PDF stem (for cache lookups).
        parser_name: Plugin name from config/plugins.yaml.
    """
    from plugins.plugin_loader import load_parser_plugin

    parser = load_parser_plugin(parser_name)
    builder = EvidenceBuilder(parser)
    confidences = builder.build(pdf_path, basename)

    print("\nSkill Confidence Scores:")
    print("-" * 44)
    for skill, conf in sorted(confidences.items(), key=lambda x: -x[1]):
        bar = "#" * int(conf * 20)
        print(f"  {skill:<24} {conf:.2f}  {bar}")

    return confidences


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python evidence_builder.py <pdf_path> <basename> [parser_name]")
        sys.exit(1)

    _pdf = Path(sys.argv[1])
    _base = sys.argv[2]
    _parser = sys.argv[3] if len(sys.argv) > 3 else "hiring-agent"
    build_evidence_graph(_pdf, _base, _parser)
