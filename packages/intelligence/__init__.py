"""
CareerOS Intelligence Core

Pure computational modules — no I/O, no DB, no external calls.
Migrated from career_os/intelligence/ (Phase 2A, 2026-07-14).
"""

from .semantic_matcher import SemanticMatcher
from .opportunity_scorer import OpportunityScorer, CareerDecisionEngine
from .gap_analyzer import GapAnalyzer, SkillGap, LearningRoadmap, LearningTask

__all__ = [
    "SemanticMatcher",
    "OpportunityScorer",
    "CareerDecisionEngine",
    "GapAnalyzer",
    "SkillGap",
    "LearningRoadmap",
    "LearningTask",
]
