"""Config loaders for CareerOS packages."""

import sys
from functools import lru_cache
from pathlib import Path

import yaml

_ROOT = Path(__file__).parents[1]


@lru_cache(maxsize=1)
def load_plugin_config() -> dict:
    """Load config/plugins.yaml (cached, relative to project root)."""
    path = _ROOT / "config" / "plugins.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Plugin config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
