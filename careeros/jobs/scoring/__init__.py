"""
CareerOS Intelligence Core

Pure computational modules — no I/O, no DB, no external calls.

SemanticMatcher is deliberately NOT re-exported here: it pulls in
sentence-transformers/torch at import time. Import it from
core.intelligence.semantic_matcher only where the semantic path is used.
"""

from careeros.jobs.scoring.opportunity_scorer import OpportunityScorer

__all__ = ["OpportunityScorer"]
