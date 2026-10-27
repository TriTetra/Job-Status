"""Resume intelligence — target-aware resume generation from evidence_items."""

from .application.resume_generator import ResumeGenerator, generate_resume

__all__ = ["ResumeGenerator", "generate_resume"]
