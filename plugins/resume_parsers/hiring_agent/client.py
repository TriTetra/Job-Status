"""
Hiring-Agent plugin — wraps services/hiring-agent/score.py.

All paths, CSV column names, and confidence weights come from
config/plugins.yaml via packages.config.load_plugin_config().
Nothing is hardcoded here.
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from plugins.plugin_interface import ResumeData, ResumeParserPlugin
from core.config import load_plugin_config

_ROOT = Path(__file__).parents[3]  # project root


class HiringAgentPlugin(ResumeParserPlugin):
    """Resume parser backed by services/hiring-agent/score.py."""

    def __init__(self) -> None:
        cfg = load_plugin_config()["resume_parsers"]["hiring-agent"]

        self._cfg = cfg
        self.install_dir = (_ROOT / cfg["install_dir"]).resolve()

        if not self.install_dir.exists():
            raise FileNotFoundError(
                f"Hiring-Agent not found at {self.install_dir}."
            )

        # Resolve venv python (Windows vs Unix)
        win_key = "venv_python_windows"
        unix_key = "venv_python_unix"
        venv_rel = cfg.get(win_key if sys.platform == "win32" else unix_key, "")
        self._venv_python = self.install_dir / venv_rel if venv_rel else None

        self._score_script = cfg["score_script"]
        self._csv_path = self.install_dir / cfg["csv_filename"]
        self._cache_dir = self.install_dir / cfg["cache_dir"]

        score_cols = set(cfg["csv_columns"]["scores"])
        meta_cols = set(cfg["csv_columns"]["metadata"])
        self._numeric_cols = score_cols | meta_cols

        self._enrichment_keys = set(cfg["enrichment_keys"])

    # ------------------------------------------------------------------
    # ResumeParserPlugin interface
    # ------------------------------------------------------------------

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "hiring-agent",
            "version": self._cfg["version"],
            "install_dir": str(self.install_dir),
            "enabled": self._cfg["enabled"],
        }

    def parse(self, pdf_path: Path, basename: str) -> ResumeData:
        self._run_score(pdf_path)
        scores = self._read_csv(basename)
        projects = self._read_github_cache(basename)
        return self._to_resume_data(scores, projects)

    def get_enrichment_payload(self, resume_data: ResumeData) -> Dict[str, Any]:
        return {
            k: resume_data.raw_scores[k]
            for k in self._enrichment_keys
            if k in resume_data.raw_scores
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_score(self, pdf_path: Path) -> None:
        python = (
            str(self._venv_python)
            if self._venv_python and self._venv_python.exists()
            else sys.executable
        )
        result = subprocess.run(
            [python, self._score_script, str(pdf_path)],
            cwd=str(self.install_dir),
            text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"score.py exited with code {result.returncode}"
            )

    def _read_csv(self, basename: str) -> Dict[str, Any]:
        if not self._csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self._csv_path}")
        with self._csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            raise ValueError("resume_evaluations.csv is empty")
        for row in reversed(rows):
            if basename in row.get("file_name", ""):
                return self._cast_row(row)
        raise ValueError(f"No CSV row for basename '{basename}'")

    def _cast_row(self, raw: Dict[str, str]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in raw.items():
            if k in self._numeric_cols:
                try:
                    out[k] = float(v)
                except (ValueError, TypeError):
                    out[k] = 0.0
            else:
                out[k] = v or None
        return out

    def _read_github_cache(self, basename: str) -> List[Dict[str, Any]]:
        path = self._cache_dir / f"githubcache_{basename}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8")).get("projects", [])

    def _to_resume_data(
        self, scores: Dict[str, Any], projects: List[Dict[str, Any]]
    ) -> ResumeData:
        def f(k: str) -> float:
            return float(scores.get(k) or 0)

        def i(k: str) -> int:
            return int(scores.get(k) or 0)

        return ResumeData(
            open_source=f("open_source_score"),
            self_projects=f("self_projects_score"),
            production=f("production_score"),
            technical_skills=f("technical_skills_score"),
            total=f("total_score"),
            total_max=f("total_max") or 100.0,
            bonus_points=f("bonus_points"),
            deductions=f("deductions"),
            total_work_experience=f("total_work_experience"),
            total_education=f("total_education"),
            total_skills=i("total_skills"),
            total_projects=i("total_projects"),
            github_repos=i("github_repos"),
            github_followers=i("github_followers"),
            github_following=i("github_following"),
            projects=projects,
            raw_scores=scores,
        )
