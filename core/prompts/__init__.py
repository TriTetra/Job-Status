"""
CareerOS Prompt Templates.

Versioned, reusable Jinja2 templates for LLM interactions.
All prompts are declarative and provider-agnostic.
"""

from .template_loader import TemplateLoader, template_loader

__all__ = ["TemplateLoader", "template_loader"]
