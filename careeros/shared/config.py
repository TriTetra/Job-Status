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


def _database_url() -> Optional[str]:
    """DATABASE_URL with the psycopg 3 driver. Coolify (and most hosts) hand out
    postgres:// or postgresql:// URLs; SQLAlchemy would pick psycopg2 for those."""
    url = os.getenv("DATABASE_URL") or None
    if url:
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _float(name: str, default: float) -> float:
    return float(os.getenv(name) or default)


def _pairs(name: str) -> dict:
    """"a=x, b=y" → {"a": "x", "b": "y"}."""
    out = {}
    for part in (os.getenv(name) or "").split(","):
        key, _, value = part.partition("=")
        if key.strip() and value.strip():
            out[key.strip()] = value.strip()
    return out


@dataclass(frozen=True)
class Settings:
    # Database
    database_url: Optional[str]
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_echo: bool
    db_connect_timeout: int

    # LLM: Anthropic (anthropic_api_key) or an OpenRouter-compatible API
    llm_provider: str                   # anthropic | openrouter (auto: whichever key is set)
    anthropic_api_key: Optional[str]
    openrouter_api_key: Optional[str]
    llm_model: str
    llm_base_url: str
    llm_fast_model: str                 # bulk extraction (cheap)
    llm_task_models: dict               # per-task overrides: {"reasoning": "anthropic/…"}
    llm_daily_budget_usd: float         # all users together; <= 0 = no limit
    llm_user_daily_budget_usd: float    # per signed-in user; <= 0 = no limit
    llm_bulk_budget_share: float        # bulk tasks stop at this share of the daily budget
    llm_max_concurrency: int
    llm_data_collection: str            # OpenRouter provider policy: deny (default) | allow

    # GitHub
    github_token: Optional[str]
    github_client_id: Optional[str]
    github_client_secret: Optional[str]
    github_redirect_uri: Optional[str]

    # Telegram notifications (a bot from @BotFather; unset = feature off)
    telegram_bot_token: Optional[str]

    # CLI: whose account `career-os jobs scan / eval / eval-sheet` use when no e-mail is given
    cli_user_email: Optional[str]

    # Adzuna job search API (developer.adzuna.com; free key): unset = the feed is off
    adzuna_app_id: Optional[str]
    adzuna_app_key: Optional[str]

    # Auth
    session_cookie_secure: bool
    token_encryption_key: Optional[str]
    e2e_auth_bypass: bool

    # Web app (redirect target after OAuth)
    web_app_url: str
    job_sync_interval_hours: float

    # Logging
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read settings once per process. Tests: get_settings.cache_clear() after changing env."""
    load_env()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or None
    provider = (os.getenv("LLM_PROVIDER") or ("anthropic" if anthropic_key else "openrouter")).strip().lower()
    # Provider defaults: interactive model / bulk model (DEFAULT_MODEL, LLM_FAST_MODEL override)
    default_model, fast_model = (
        ("claude-opus-5-5", "claude-haiku-5-5") if provider == "anthropic" else ("openai/gpt-4o-mini", None)
    )
    fast_model = fast_model or default_model
    return Settings(
        database_url=_database_url(),
        # A handful of users and one API worker: small pool by default
        db_pool_size=_int("DB_POOL_SIZE", 5),
        db_max_overflow=_int("DB_MAX_OVERFLOW", 5),
        db_pool_timeout=_int("DB_POOL_TIMEOUT", 30),
        db_echo=_bool("DB_ECHO"),
        db_connect_timeout=_int("DB_CONNECT_TIMEOUT", 5),
        llm_provider=provider,
        anthropic_api_key=anthropic_key,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
        llm_model=os.getenv("DEFAULT_MODEL") or default_model,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        # Bulk work stays on the cheap model unless LLM_FAST_MODEL says otherwise (OpenRouter:
        # same as the main model by default)
        llm_fast_model=os.getenv("LLM_FAST_MODEL") or (
            fast_model if provider == "anthropic" else (os.getenv("DEFAULT_MODEL") or default_model)),
        llm_task_models=_pairs("LLM_TASK_MODELS"),
        llm_daily_budget_usd=_float("LLM_DAILY_BUDGET_USD", 2.0),
        llm_user_daily_budget_usd=_float("LLM_USER_DAILY_BUDGET_USD", 0.5),
        llm_bulk_budget_share=_float("LLM_BULK_BUDGET_SHARE", 0.7),
        llm_max_concurrency=_int("LLM_MAX_CONCURRENCY", 4),
        # "deny": only providers that don't store or train on prompts (CVs are personal data)
        llm_data_collection=(os.getenv("LLM_DATA_COLLECTION") or "deny").strip().lower(),
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_client_id=os.getenv("GITHUB_CLIENT_ID") or None,
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET") or None,
        # Default: the site's own callback (the web app proxies /api to the API)
        github_redirect_uri=os.getenv("GITHUB_REDIRECT_URI")
        or os.getenv("WEB_APP_URL", "http://localhost:3000").rstrip("/") + "/api/oauth/github/callback",
        telegram_bot_token=(os.getenv("TELEGRAM_BOT_TOKEN") or "").strip() or None,
        cli_user_email=(os.getenv("CAREER_OS_EMAIL") or "").strip() or None,
        adzuna_app_id=(os.getenv("ADZUNA_APP_ID") or "").strip() or None,
        adzuna_app_key=(os.getenv("ADZUNA_APP_KEY") or "").strip() or None,
        # Secure cookies also work on http://localhost in current browsers; set false only for odd dev setups
        session_cookie_secure=_bool("SESSION_COOKIE_SECURE", True),
        token_encryption_key=os.getenv("TOKEN_ENCRYPTION_KEY") or None,
        e2e_auth_bypass=os.getenv("CAREEROS_E2E_AUTH_BYPASS") == "1",
        web_app_url=os.getenv("WEB_APP_URL", "http://localhost:3000").rstrip("/"),
        # Company board sync + rescore inside the API process; 0 = off (run `career-os jobs sync` yourself)
        job_sync_interval_hours=float(os.getenv("JOB_SYNC_INTERVAL_HOURS") or 0),
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
