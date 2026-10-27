"""
Adapter: hiring-agent plugin -> career_scores PostgreSQL table.

Public API:
    score_resume(pdf_path)              -> ResumeData
    build_and_enrich(pdf_path, session) -> runs plugin + evidence graph + enriches DB
    enrich_career_scores(session, data) -> writes resume_score into explanation JSONB
    HiringAgentAdapter(pdf_path).run()  -> ResumeData (backward compat)

All config (paths, CSV columns, enrichment keys) comes from
config/plugins.yaml via the HiringAgentPlugin.
"""

import logging
from pathlib import Path
from typing import Any

from plugins.plugin_interface import ResumeData
from plugins.resume_parsers.hiring_agent import HiringAgentPlugin

logger = logging.getLogger(__name__)


class HiringAgentAdapter:
    """Thin OO wrapper around the plugin for backward compatibility."""

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path).resolve()
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"CV not found: {self.pdf_path}")
        self._plugin = HiringAgentPlugin()

    def run(self) -> ResumeData:
        """Run hiring-agent and return structured ResumeData."""
        return self._plugin.parse(self.pdf_path, self.pdf_path.stem)


def score_resume(pdf_path: str | Path) -> ResumeData:
    """One-liner: run hiring-agent on pdf_path, return ResumeData."""
    return HiringAgentAdapter(pdf_path).run()


def build_and_enrich(pdf_path: str | Path, session) -> ResumeData:
    """
    Full pipeline:
      1. Parse resume via plugin (score.py + CSV + GitHub cache)
      2. Build Evidence Graph -> write evidence rows to DB
      3. Enrich career_scores.explanation with resume_score payload

    Returns ResumeData from the plugin.
    """
    plugin = HiringAgentPlugin()
    pdf_path = Path(pdf_path).resolve()
    basename = pdf_path.stem

    logger.info("Parsing resume")
    resume_data = plugin.parse(pdf_path, basename)

    logger.info("Building Evidence Graph")
    from services.resume_intelligence.application.evidence_builder import (
        EvidenceBuilder,
    )
    builder = EvidenceBuilder(plugin)
    confidences = builder._write_to_db(builder._extract_records(resume_data))

    logger.info("Enriching career_scores")
    payload = plugin.get_enrichment_payload(resume_data)
    payload["skill_confidence"] = confidences
    n = _enrich_db(session, payload)
    logger.info("Updated %d career_score rows", n)

    return resume_data


def enrich_career_scores(session, resume_data: ResumeData) -> int:
    """
    Merge resume_data enrichment fields into career_scores.explanation.
    Returns number of rows updated.
    """
    plugin = HiringAgentPlugin()
    payload = plugin.get_enrichment_payload(resume_data)
    return _enrich_db(session, payload)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _enrich_db(session, enrichment: dict[str, Any]) -> int:
    from sqlalchemy import select
    from core.db.models.career_score import CareerScore

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
