"""careeros.shared.config — env loading and typed settings."""

import pytest

from careeros.shared import config as cfg
from careeros.shared.config import get_settings, load_env


@pytest.fixture
def fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_load_env_does_not_override_process_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('ALREADY_SET=from_file\nNEW_ONE="quoted value"\n# comment\nBROKEN_LINE\n', encoding="utf-8")
    monkeypatch.setenv("ALREADY_SET", "from_process")
    monkeypatch.delenv("NEW_ONE", raising=False)

    load_env(env)

    import os
    assert os.environ["ALREADY_SET"] == "from_process"
    assert os.environ["NEW_ONE"] == "quoted value"
    monkeypatch.delenv("NEW_ONE")


def test_settings_defaults(monkeypatch, fresh_settings):
    for var in ("DB_POOL_SIZE", "DEFAULT_MODEL", "LLM_BASE_URL", "LOG_LEVEL", "CAREEROS_E2E_AUTH_BYPASS"):
        monkeypatch.delenv(var, raising=False)
    s = get_settings()
    assert s.db_pool_size == 5
    assert s.db_connect_timeout == 5
    assert s.llm_model == "openai/gpt-4o-mini"
    assert s.llm_base_url == "https://openrouter.ai/api/v1"
    assert s.log_level == "INFO"
    assert s.e2e_auth_bypass is False


def test_settings_read_env(monkeypatch, fresh_settings):
    monkeypatch.setenv("DB_POOL_SIZE", "3")
    monkeypatch.setenv("DB_ECHO", "true")
    monkeypatch.setenv("LLM_BASE_URL", "https://x.example/v1/")
    monkeypatch.setenv("CAREEROS_E2E_AUTH_BYPASS", "1")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    s = get_settings()
    assert s.db_pool_size == 3
    assert s.db_echo is True
    assert s.llm_base_url == "https://x.example/v1"
    assert s.e2e_auth_bypass is True
    assert s.log_level == "DEBUG"


def test_empty_secrets_are_none(monkeypatch, fresh_settings):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    s = get_settings()
    assert s.openrouter_api_key is None


def test_settings_are_immutable(fresh_settings):
    with pytest.raises(Exception):
        get_settings().db_pool_size = 99


def test_load_config_substitutes_env(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("llm:\n  api_key: ${MY_TEST_KEY}\ncandidate:\n  name: Ada\n", encoding="utf-8")
    monkeypatch.setenv("MY_TEST_KEY", "secret-123")
    conf = cfg.load_config(path)
    assert conf["llm"]["api_key"] == "secret-123"
    assert conf["user"]["id"] == "default"


def test_plugin_config_loads():
    assert "job_sources" in cfg.load_plugin_config()
