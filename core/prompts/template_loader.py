"""
Jinja2 template loader — singleton pattern.

Usage:
    from core.prompts import template_loader

    output = template_loader.render(
        "resume/tailor_for_target.jinja",
        target_company="Google",
        target_title="ML Engineer",
        evidence_summary="...",
    )
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateLoader:
    """
    Singleton Jinja2 template loader.

    Features:
    - Lazy loading (templates loaded on first use)
    - Cached environment (no re-parsing)
    - Provider-agnostic (works with any LLM)
    """

    _instance = None
    _env = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        prompts_dir = Path(__file__).parent

        self._env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        self._env.filters["join_skills"] = lambda skills: ", ".join(skills) if skills else "None"
        self._env.filters["truncate_text"] = lambda text, length=200: (
            text[:length] + "..." if len(text) > length else text
        )

    def render(self, template_path: str, **context) -> str:
        """
        Render template with context.

        Args:
            template_path: Relative path to template (e.g., "resume/tailor_for_target.jinja")
            **context: Template variables

        Returns:
            Rendered template string
        """
        template = self._env.get_template(template_path)
        return template.render(**context)

    def list_templates(self) -> list:
        return self._env.list_templates()


template_loader = TemplateLoader()
