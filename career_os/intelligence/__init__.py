"""Intelligence modules for Career OS."""

from .semantic_matcher import SemanticMatcher
from .gap_analyzer import GapAnalyzer, SkillGap, LearningRoadmap
from .opportunity_scorer import OpportunityScorer, CareerDecisionEngine

__all__ = [
    'SemanticMatcher',
    'GapAnalyzer',
    'SkillGap',
    'LearningRoadmap',
    'OpportunityScorer',
    'CareerDecisionEngine',
]
