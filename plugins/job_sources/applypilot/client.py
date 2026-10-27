"""
ApplyPilot SQLite client.

ApplyPilotClient  — low-level DB I/O only, no business logic.
ApplyPilotPlugin  — high-level JobSourcePlugin implementation.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import load_plugin_config
from plugins.plugin_interface import JobSourcePlugin


class ApplyPilotClient:
    """Low-level SQLite reader for the ApplyPilot database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path.resolve()
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"ApplyPilot database not found at {self.db_path}"
            )

    def fetch_jobs(
        self,
        hours_old: int = 72,
        min_score: int = 7,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs ordered by fit_score DESC.

        Args:
            hours_old: Only jobs discovered in last N hours (0 = all).
            min_score: Minimum fit_score.
            limit: Max rows (None = all).
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            if hours_old > 0:
                from datetime import datetime, timedelta, timezone
                cutoff = (
                    datetime.now(timezone.utc) - timedelta(hours=hours_old)
                ).isoformat()
                query = """
                    SELECT *
                    FROM jobs
                    WHERE fit_score >= ?
                      AND discovered_at >= ?
                    ORDER BY fit_score DESC, discovered_at DESC
                """
                params: list = [min_score, cutoff]
            else:
                # hours_old=0 → all time, no time filter
                query = """
                    SELECT * FROM jobs
                    WHERE fit_score >= ?
                    ORDER BY fit_score DESC, discovered_at DESC
                """
                params = [min_score]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_urls(self) -> set:
        """Return set of all URLs in the database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            return {r[0] for r in conn.execute("SELECT url FROM jobs").fetchall()}
        finally:
            conn.close()

    def count_jobs(self, min_score: int = 0) -> int:
        """Count jobs with optional score filter."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE fit_score >= ?", [min_score]
            ).fetchone()[0]
        finally:
            conn.close()


class ApplyPilotPlugin(JobSourcePlugin):
    """
    ApplyPilot job source plugin.

    Reads jobs from ~/.applypilot/applypilot.db (path configurable in
    config/plugins.yaml → job_sources.applypilot.db_path).
    """

    def __init__(self) -> None:
        from .adapter import ApplyPilotAdapter

        cfg = load_plugin_config()["job_sources"]["applypilot"]
        self._cfg = cfg

        # Resolve ~ in db_path
        raw = cfg["db_path"]
        db_path = (
            Path.home() / raw[2:].lstrip("/\\")
            if raw.startswith("~")
            else Path(raw)
        )

        self.client = ApplyPilotClient(db_path)
        self.adapter = ApplyPilotAdapter(cfg)

    # ------------------------------------------------------------------
    # JobSourcePlugin interface
    # ------------------------------------------------------------------

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "applypilot",
            "version": self._cfg["version"],
            "description": self._cfg["description"],
            "enabled": self._cfg["enabled"],
            "db_path": str(self.client.db_path),
            "job_count": self.client.count_jobs(),
        }

    def scan(self, hours_old: int = 72, min_score: int = 7) -> List[Dict[str, Any]]:
        """Return raw rows from ApplyPilot DB."""
        return self.client.fetch_jobs(hours_old=hours_old, min_score=min_score)

    def normalize(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a raw DB row to the canonical Job schema."""
        return self.adapter.normalize(raw_job)
