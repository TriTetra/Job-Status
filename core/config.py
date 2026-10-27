"""Config loaders for CareerOS packages."""

import os
import re
from functools import lru_cache
from pathlib import Path

import yaml

_ROOT = Path(__file__).parents[1]


@lru_cache(maxsize=1)
def load_plugin_config() -> dict:
    """Load config/plugins.yaml (cached, relative to project root)."""
    path = _ROOT / "infra" / "config" / "plugins.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Plugin config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── config.yaml (candidate / llm settings) ────────────────────────────────

def _substitute_env_vars(text: str) -> str:
    """Replace ${VAR_NAME} with os.environ values."""
    def replacer(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if not value:
            print(f"WARNING: env var {var_name} not set — check your .env file")
            return ""
        return value
    return re.sub(r'\$\{([^}]+)\}', replacer, text)


def load_dotenv(env_path: Path | None = None) -> None:
    """Minimal .env loader — no external dependency required."""
    path = env_path or (_ROOT / ".env")
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def load_config(config_path: Path | None = None) -> dict:
    """
    Load config.yaml from project root (or given path).
    Substitutes ${ENV_VAR} placeholders from environment / .env file.
    """
    load_dotenv()

    path = config_path or (_ROOT / "config.yaml")

    if not path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {path}. "
            "Copy config.yaml.example to config.yaml and fill in your values."
        )

    raw = path.read_text(encoding="utf-8")
    substituted = _substitute_env_vars(raw)
    config = yaml.safe_load(substituted)

    # Ensure user.id always exists
    if "user" not in config:
        config["user"] = {}
    if "id" not in config["user"]:
        config["user"]["id"] = "default"

    return config
