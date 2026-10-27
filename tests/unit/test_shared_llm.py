"""careeros.shared.llm — the single LLM client. HTTP is faked; nothing leaves the process."""

import pytest
import requests

from careeros.shared import llm as llm_mod
from careeros.shared.config import get_settings
from careeros.shared.llm import LLMClient, LLMError, LLMNotConfiguredError, get_llm_client, parse_json


class FakeResponse:
    def __init__(self, status=200, content="ok", body=None):
        self.status_code = status
        self._body = body if body is not None else {"choices": [{"message": {"content": content}}]}
        self.text = str(self._body)

    def json(self):
        return self._body


class FakeSession:
    """Returns queued responses (or raises queued exceptions) and records payloads."""

    def __init__(self, *responses):
        self.queue = list(responses)
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)


def _client(*responses, **kw):
    session = FakeSession(*responses)
    return LLMClient("sk-test", "test/model", "https://llm.example/api/v1/", session=session, **kw), session


# ── request shape ─────────────────────────────────────────────────────────

def test_complete_builds_openai_style_payload():
    client, session = _client(FakeResponse(content="  hello  "))
    out = client.complete("hi", system="sys", temperature=0.1, max_tokens=50, timeout=7)

    assert out == "hello"
    call = session.calls[0]
    assert call["url"] == "https://llm.example/api/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer sk-test"
    assert call["timeout"] == 7
    assert call["json"] == {
        "model": "test/model",
        "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        "temperature": 0.1,
        "max_tokens": 50,
    }


def test_no_system_message_when_not_given():
    client, session = _client(FakeResponse())
    client.complete("hi")
    assert session.calls[0]["json"]["messages"] == [{"role": "user", "content": "hi"}]


def test_json_mode_sets_response_format():
    client, session = _client(FakeResponse(content='{"a": 1}'))
    assert client.complete_json("x", json_mode=True) == {"a": 1}
    assert session.calls[0]["json"]["response_format"] == {"type": "json_object"}


# ── retries ───────────────────────────────────────────────────────────────

def test_retries_transient_http_then_succeeds():
    client, session = _client(FakeResponse(status=429), FakeResponse(status=503), FakeResponse(content="done"))
    assert client.complete("x") == "done"
    assert len(session.calls) == 3


def test_retries_timeouts_then_raises_llm_error():
    client, session = _client(requests.Timeout("t1"), requests.Timeout("t2"), requests.Timeout("t3"))
    with pytest.raises(LLMError, match="request failed"):
        client.complete("x")
    assert len(session.calls) == 3


def test_client_errors_are_not_retried():
    client, session = _client(FakeResponse(status=401, body={"error": "bad key"}))
    with pytest.raises(LLMError, match="401"):
        client.complete("x")
    assert len(session.calls) == 1


def test_gives_up_after_max_retries_on_5xx():
    client, session = _client(FakeResponse(status=500), FakeResponse(status=500), max_retries=1)
    with pytest.raises(LLMError, match="500"):
        client.complete("x")
    assert len(session.calls) == 2


def test_unexpected_response_shape_raises_llm_error():
    client, _ = _client(FakeResponse(body={"oops": True}))
    with pytest.raises(LLMError, match="shape"):
        client.complete("x")


def test_llm_error_is_a_runtime_error():
    """Callers that historically caught RuntimeError keep working."""
    assert issubclass(LLMError, RuntimeError)


# ── JSON parsing ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("text, expected", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": 1}\n```', {"a": 1}),
    ('```\n[1, 2]\n```', [1, 2]),
    ('  \n{"a": 1}  ', {"a": 1}),
])
def test_parse_json_tolerates_fences(text, expected):
    assert parse_json(text) == expected


def test_parse_json_raises_llm_error_on_garbage():
    with pytest.raises(LLMError, match="invalid JSON"):
        parse_json("sure! here you go")


# ── factory ───────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_factory():
    get_settings.cache_clear()
    get_llm_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_llm_client.cache_clear()


def test_factory_raises_not_configured_without_key(monkeypatch, fresh_factory):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(LLMNotConfiguredError):
        get_llm_client()


def test_factory_uses_settings(monkeypatch, fresh_factory):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-from-env")
    monkeypatch.setenv("DEFAULT_MODEL", "some/model")
    client = get_llm_client()
    assert client.model == "some/model"
    assert get_llm_client() is client  # cached per process
