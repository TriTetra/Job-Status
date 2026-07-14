"""Plugin loader — factory for resume parser and job source plugins."""

from typing import Any, Dict

from packages.config import load_plugin_config
from plugins.plugin_interface import JobSourcePlugin, ResumeParserPlugin


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


def load_job_source_plugin(plugin_name: str = "applypilot") -> JobSourcePlugin:
    """
    Instantiate and return a job source plugin by name.

    Args:
        plugin_name: Key under job_sources in config/plugins.yaml.

    Raises:
        ValueError: Plugin not found in config, or disabled.
        NotImplementedError: Plugin name has no implementation yet.
    """
    sources = load_plugin_config().get("job_sources", {})

    if plugin_name not in sources:
        raise ValueError(
            f"Job source '{plugin_name}' not found in config/plugins.yaml. "
            f"Available: {list(sources)}"
        )

    if not sources[plugin_name].get("enabled", False):
        raise ValueError(f"Job source '{plugin_name}' is disabled in config.")

    if plugin_name == "applypilot":
        from plugins.job_sources.applypilot import ApplyPilotPlugin
        return ApplyPilotPlugin()

    raise NotImplementedError(
        f"Job source '{plugin_name}' has no implementation. "
        "Add it to plugins/job_sources/ and register it here."
    )


def list_available_job_sources() -> Dict[str, Any]:
    """Return metadata for all configured job source plugins."""
    sources = load_plugin_config().get("job_sources", {})
    return {
        name: {
            "enabled": cfg.get("enabled", False),
            "version": cfg.get("version", "unknown"),
            "description": cfg.get("description", ""),
        }
        for name, cfg in sources.items()
    }
