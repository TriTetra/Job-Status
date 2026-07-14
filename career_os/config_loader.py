"""
Config loader — reads config.yaml with environment variable substitution.

Usage:
    from career_os.config_loader import load_config
    config = load_config()
    api_key = config['llm']['api_key']
"""

import os
import re
import yaml
from pathlib import Path


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
    path = env_path or (Path(__file__).parent.parent / ".env")
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

    path = config_path or (Path(__file__).parent.parent / "config.yaml")

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
