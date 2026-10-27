"""The one LLM client (OpenRouter-compatible chat completions).

    from careeros.shared.llm import get_llm_client
    llm = get_llm_client()                        # raises LLMNotConfiguredError without a key
    text = llm.complete("…", system="…", max_tokens=200)
    data = llm.complete_json("…", max_tokens=2000)   # parsed JSON, ``` fences tolerated

Transient failures (timeouts, connection errors, HTTP 429/5xx) are retried
with exponential backoff; anything else raises immediately.
"""

import json
import logging
import re
import time
from functools import lru_cache
from typing import Any, Optional

import requests

from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$")


class LLMError(RuntimeError):
    """The LLM call failed or returned something unusable."""


class LLMNotConfiguredError(LLMError):
    """No API key — callers with a non-LLM fallback should catch this."""


def parse_json(text: str) -> Any:
    """Parse model output as JSON, tolerating ```json fences around it."""
    cleaned = _FENCE_RE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM returned invalid JSON: {e}; head={cleaned[:120]!r}") from e


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        *,
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.model = model
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://career-os.local",
            "X-Title": "CareerOS",
        }
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._http = session or requests.Session()

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False,
        timeout: float = 60,
    ) -> str:
        """Return the assistant message text (stripped)."""
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        body = self._post(payload, timeout)
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            raise LLMError(f"Unexpected LLM response shape: {str(body)[:200]}") from e

    def complete_json(self, prompt: str, **kwargs: Any) -> Any:
        """complete() + parse_json(). Pass json_mode=True to force a JSON object."""
        return parse_json(self.complete(prompt, **kwargs))

    def _post(self, payload: dict, timeout: float) -> dict:
        for attempt in range(self._max_retries + 1):
            last = attempt == self._max_retries
            try:
                resp = self._http.post(self._url, json=payload, headers=self._headers, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                if last:
                    raise LLMError(f"LLM request failed: {e}") from e
                self._sleep(attempt, reason=type(e).__name__)
                continue
            if resp.status_code in _RETRYABLE_STATUS and not last:
                self._sleep(attempt, reason=f"HTTP {resp.status_code}")
                continue
            if resp.status_code >= 400:
                raise LLMError(f"LLM HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()
        raise AssertionError("unreachable")

    def _sleep(self, attempt: int, reason: str) -> None:
        delay = self._backoff * (2 ** attempt)
        logger.warning("LLM call %s — retry %d/%d in %.1fs", reason, attempt + 1, self._max_retries, delay)
        time.sleep(delay)


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Process-wide client built from settings."""
    s = get_settings()
    if not s.openrouter_api_key:
        raise LLMNotConfiguredError("OPENROUTER_API_KEY not set")
    return LLMClient(api_key=s.openrouter_api_key, model=s.llm_model, base_url=s.llm_base_url)
