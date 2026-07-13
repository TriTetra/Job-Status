"""Backward compatibility shim — redirects to packages.intelligence."""

from packages.intelligence import (
    SemanticMatcher,
    OpportunityScorer,
    CareerDecisionEngine,
    GapAnalyzer,
    SkillGap,
    LearningRoadmap,
    LearningTask,
)

__all__ = [
    "SemanticMatcher",
    "OpportunityScorer",
    "CareerDecisionEngine",
    "GapAnalyzer",
    "SkillGap",
    "LearningRoadmap",
    "LearningTask",
]
