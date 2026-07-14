"""Plugin loader — factory for resume parser plugins."""

from typing import Any, Dict

from packages.config import load_plugin_config
from plugins.plugin_interface import ResumeParserPlugin


def load_parser_plugin(parser_name: str = "hiring-agent") -> ResumeParserPlugin:
    """
    Instantiate and return a resume parser plugin by name.

    Args:
        parser_name: Key under resume_parsers in config/plugins.yaml.

    Raises:
        ValueError: Plugin not found in config, or disabled.
        NotImplementedError: Plugin name has no implementation yet.
    """
    parsers = load_plugin_config().get("resume_parsers", {})

    if parser_name not in parsers:
        raise ValueError(
            f"Parser '{parser_name}' not found in config/plugins.yaml. "
            f"Available: {list(parsers)}"
        )

    if not parsers[parser_name].get("enabled", False):
        raise ValueError(f"Parser '{parser_name}' is disabled in config.")

    if parser_name == "hiring-agent":
        from plugins.resume_parsers.hiring_agent import HiringAgentPlugin
        return HiringAgentPlugin()

    raise NotImplementedError(
        f"Parser '{parser_name}' has no implementation. "
        "Add it to plugins/resume_parsers/ and register it here."
    )


def list_available_parsers() -> Dict[str, Any]:
    """Return metadata for all configured resume parsers."""
    parsers = load_plugin_config().get("resume_parsers", {})
    return {
        name: {
            "enabled": cfg.get("enabled", False),
            "version": cfg.get("version", "unknown"),
        }
        for name, cfg in parsers.items()
    }
