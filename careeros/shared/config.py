"""The single place configuration is read from.

Sources, in priority order:
  1. Process environment
  2. `.env` at the repo root (loaded once; never overrides 1.)
  3. Defaults below

Plus two YAML files with structured config:
  - infra/config/plugins.yaml  → load_plugin_config()
  - config.yaml (candidate / resume preferences) → load_config()

Code should call get_settings() instead of reading os.environ directly.
"""

import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]


# ── .env ──────────────────────────────────────────────────────────────────

_env_loaded = False


def load_env(env_path: Optional[Path] = None) -> None:
    """Load KEY=VALUE pairs from `.env` into os.environ (existing vars win). Idempotent."""
    global _env_loaded
    if _env_loaded and env_path is None:
        return
    path = env_path or ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    if env_path is None:
        _env_loaded = True


# ── typed settings ────────────────────────────────────────────────────────

def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    # Database
    database_url: Optional[str]
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_echo: bool
    db_connect_timeout: int

    # LLM (OpenRouter-compatible chat completions API)
    openrouter_api_key: Optional[str]
    llm_model: str
    llm_base_url: str

    # GitHub
    github_token: Optional[str]
    github_client_id: Optional[str]
    github_client_secret: Optional[str]
    github_redirect_uri: Optional[str]

    # Auth
    session_cookie_secure: bool
    token_encryption_key: Optional[str]
    e2e_auth_bypass: bool

    # Web app (redirect target after OAuth)
    web_app_url: str

    # Logging
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read settings once per process. Tests: get_settings.cache_clear() after changing env."""
    load_env()
    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        # A handful of users and one API worker: small pool by default
        db_pool_size=_int("DB_POOL_SIZE", 5),
        db_max_overflow=_int("DB_MAX_OVERFLOW", 5),
        db_pool_timeout=_int("DB_POOL_TIMEOUT", 30),
        db_echo=_bool("DB_ECHO"),
        db_connect_timeout=_int("DB_CONNECT_TIMEOUT", 5),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
        llm_model=os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini"),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_client_id=os.getenv("GITHUB_CLIENT_ID") or None,
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET") or None,
        github_redirect_uri=os.getenv("GITHUB_REDIRECT_URI") or None,
        # Secure cookies also work on http://localhost in current browsers; set false only for odd dev setups
        session_cookie_secure=_bool("SESSION_COOKIE_SECURE", True),
        token_encryption_key=os.getenv("TOKEN_ENCRYPTION_KEY") or None,
        e2e_auth_bypass=os.getenv("CAREEROS_E2E_AUTH_BYPASS") == "1",
        web_app_url=os.getenv("WEB_APP_URL", "http://localhost:3000").rstrip("/"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


# ── YAML config ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_plugin_config() -> dict:
    """infra/config/plugins.yaml (cached)."""
    path = ROOT / "infra" / "config" / "plugins.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Plugin config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _substitute_env_vars(text: str) -> str:
    """Replace ${VAR_NAME} with os.environ values."""
    def replacer(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if not value:
            logger.warning("config.yaml references ${%s}, which is not set", var_name)
            return ""
        return value
    return re.sub(r"\$\{([^}]+)\}", replacer, text)


def load_config(config_path: Optional[Path] = None) -> dict:
    """config.yaml at the repo root (candidate profile, resume preferences).

    ${ENV_VAR} placeholders are substituted from the environment / .env.
    """
    load_env()
    path = config_path or ROOT / "config.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {path}. "
            "Copy config.yaml.example to config.yaml and fill in your values."
        )
    config = yaml.safe_load(_substitute_env_vars(path.read_text(encoding="utf-8")))
    config.setdefault("user", {}).setdefault("id", "default")
    return config
