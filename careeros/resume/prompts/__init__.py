"""
CareerOS Prompt Templates.

Versioned, reusable Jinja2 templates for LLM interactions.
All prompts are declarative and provider-agnostic.
"""

from careeros.resume.prompts.template_loader import TemplateLoader, template_loader

__all__ = ["TemplateLoader", "template_loader"]
