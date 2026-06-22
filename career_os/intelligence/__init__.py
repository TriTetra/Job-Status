"""Intelligence modules for Career OS."""

from .semantic_matcher import SemanticMatcher
from .gap_analyzer import GapAnalyzer, SkillGap, LearningRoadmap

__all__ = [
    'SemanticMatcher',
    'GapAnalyzer',
    'SkillGap',
    'LearningRoadmap',
]
