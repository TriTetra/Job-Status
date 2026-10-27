"""Plugin loader — factory for job source plugins."""

from typing import Any, Dict

from shared.config import load_plugin_config
from plugins.plugin_interface import JobSourcePlugin


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
